-- ======================================================
-- Archery Club Database - Stored Procedures & Indexes
-- ======================================================
-- ======================================================
-- CREATE INDEXES
-- ======================================================

-- Score table indexes - Critical for archer score retrieval and competition results
CREATE INDEX idx_score_archer ON Score(ArcherID);
CREATE INDEX idx_score_archer_date ON Score(ArcherID, Date);

-- CompetitionScore table - Essential for competition result queries
CREATE INDEX idx_compscore_competition ON CompetitionScore(CompetitionID);

-- End and Arrow tables - Needed for retrieving score details
CREATE INDEX idx_end_score ON End(ScoreID);
CREATE INDEX idx_end_range_sequence ON End(ScoreID, RangeSequence, EndSequence);
CREATE INDEX idx_arrow_end ON Arrow(EndID);

-- StagedScore table - For score approval process
CREATE INDEX idx_stagedscore_archer ON StagedScore(ArcherID);
CREATE INDEX idx_stagedscore_date ON StagedScore(Date);

-- Archer table - For class determination
CREATE INDEX idx_archer_gender_dob ON Archer(Gender, DateOfBirth);

-- RoundRange table - For round definition lookups
CREATE INDEX idx_roundrange_round ON RoundRange(RoundID);

CREATE INDEX idx_securitylog_eventtime ON SecurityLog(EventTime);
CREATE INDEX idx_securitylog_userid ON SecurityLog(UserID);
CREATE INDEX idx_securitylog_eventtype ON SecurityLog(EventType);
CREATE INDEX idx_securitylog_severity ON SecurityLog(Severity);
CREATE INDEX idx_securitylog_isreviewed ON SecurityLog(IsReviewed);

-- ======================================================
-- USE CASE 1: View Personal Scores
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspGetArcherScores(
    IN p_ArcherID INT,
    IN p_StartDate DATE,
    IN p_EndDate DATE,
    IN p_RoundID INT
)
BEGIN
    -- View all scores for an archer with optional filters
    SELECT s.ScoreID, s.Date, r.RoundName, s.TotalScore, e.Name AS Equipment, 
           s.IsCompetition, s.IsApproved
    FROM Score s
    JOIN Round r ON s.RoundID = r.RoundID
    JOIN EquipmentType e ON s.EquipmentTypeID = e.EquipmentTypeID
    WHERE s.ArcherID = p_ArcherID
      AND (p_StartDate IS NULL OR s.Date >= p_StartDate)
      AND (p_EndDate IS NULL OR s.Date <= p_EndDate)
      AND (p_RoundID IS NULL OR s.RoundID = p_RoundID)
    ORDER BY s.Date DESC;
END //
DELIMITER ;

-- ======================================================
-- USE CASE 2: Record Practice Score
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspAddStagedScore(
    IN p_ArcherID INT,
    IN p_RoundID INT,
    IN p_EquipmentTypeID INT,
    IN p_Date DATE,
    IN p_TotalScore INT,
    OUT p_StagedScoreID INT
)
BEGIN
    -- Add a new score to the staged table
    INSERT INTO StagedScore (ArcherID, RoundID, EquipmentTypeID, Date, TotalScore, SubmissionDate)
    VALUES (p_ArcherID, p_RoundID, p_EquipmentTypeID, p_Date, p_TotalScore, NOW());
    
    -- Return the new staged score ID
    SET p_StagedScoreID = LAST_INSERT_ID();
END //
DELIMITER ;

-- ======================================================
-- USE CASE 3: View Round Definitions
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspGetRoundDetails(
    IN p_RoundID INT
)
BEGIN
    -- Get round information with ranges
    SELECT r.RoundName, r.TotalArrows, r.PossibleScore, r.Description,
           rr.RangeSequence, rr.Distance, rr.NumberOfEnds, rr.ArrowsPerEnd,
           tf.Size AS TargetFaceSize, tf.Description AS TargetFaceDescription
    FROM Round r
    JOIN RoundRange rr ON r.RoundID = rr.RoundID
    JOIN TargetFace tf ON rr.TargetFaceID = tf.TargetFaceID
    WHERE r.RoundID = p_RoundID
    ORDER BY rr.RangeSequence;
    
    -- Get equivalent rounds where this round is the base round
    SELECT 'This round is base for:' AS EquivalentType,
           c.ClassName, et.Name AS EquipmentType, 
           equiv_r.RoundName AS EquivalentRoundName,
           er.EffectiveDate, er.ExpiryDate
    FROM EquivalentRound er
    JOIN Class c ON er.ClassID = c.ClassID
    JOIN EquipmentType et ON er.EquipmentTypeID = et.EquipmentTypeID
    JOIN Round equiv_r ON er.EquivalentRoundRefID = equiv_r.RoundID
    WHERE er.BaseRoundID = p_RoundID
    AND (er.ExpiryDate IS NULL OR er.ExpiryDate >= CURDATE())
    
    UNION ALL
    
    -- Get base rounds where this round is an equivalent
    SELECT 'This round is equivalent to:' AS EquivalentType,
           c.ClassName, et.Name AS EquipmentType,
           base_r.RoundName AS EquivalentRoundName,
           er.EffectiveDate, er.ExpiryDate
    FROM EquivalentRound er
    JOIN Class c ON er.ClassID = c.ClassID
    JOIN EquipmentType et ON er.EquipmentTypeID = et.EquipmentTypeID
    JOIN Round base_r ON er.BaseRoundID = base_r.RoundID
    WHERE er.EquivalentRoundRefID = p_RoundID
    AND (er.ExpiryDate IS NULL OR er.ExpiryDate >= CURDATE())
    
    ORDER BY EquivalentType, ClassName, EquipmentType;
END //
DELIMITER ;

-- ======================================================
-- USE CASE 4: View Competition Results (Modified)
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspGetCompetitionResults(
    IN p_CompetitionID INT
)
BEGIN
    -- Get results with competition details and archer categories in one result set
    SELECT c.CompetitionID, c.CompetitionName, c.Date, 
           IF(c.IsChampionship, 'Yes', 'No') AS IsChampionship,
           c.Description,
           CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName,
           cls.ClassName, et.Name AS EquipmentType,
           CONCAT(cls.ClassName, ' ', et.Name) AS Category,
           r.RoundName, s.TotalScore,
           r.PossibleScore,
           ROUND(s.TotalScore / r.PossibleScore * 100, 2) AS ScorePercentage
    FROM CompetitionScore cs
    JOIN Competition c ON cs.CompetitionID = c.CompetitionID
    JOIN Score s ON cs.ScoreID = s.ScoreID
    JOIN Archer a ON s.ArcherID = a.ArcherID
    JOIN Round r ON s.RoundID = r.RoundID
    JOIN EquipmentType et ON s.EquipmentTypeID = et.EquipmentTypeID
    -- Join to determine archer's class based on age and gender
    JOIN Class cls ON (
        a.Gender = cls.Gender AND
        (SELECT ag.AgeGroupID 
         FROM AgeGroup ag 
         WHERE (YEAR(c.Date) - YEAR(a.DateOfBirth)) BETWEEN IFNULL(ag.MinAge, 0) AND IFNULL(ag.MaxAge, 999)
         LIMIT 1) = cls.AgeGroupID
    )
    WHERE cs.CompetitionID = p_CompetitionID
    ORDER BY Category, ScorePercentage DESC;
END //
DELIMITER ;

-- ======================================================
-- USE CASE 5: Manage Archers
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspAddArcher(
    IN p_FirstName VARCHAR(50),
    IN p_LastName VARCHAR(50),
    IN p_DateOfBirth DATE,
    IN p_Gender CHAR(1),
    IN p_DefaultEquipmentTypeID INT,
    OUT p_ArcherID INT
)
BEGIN
    -- Add a new archer
    INSERT INTO Archer (FirstName, LastName, DateOfBirth, Gender, DefaultEquipmentTypeID, IsActive)
    VALUES (p_FirstName, p_LastName, p_DateOfBirth, p_Gender, p_DefaultEquipmentTypeID, TRUE);
    
    -- Return the new archer ID
    SET p_ArcherID = LAST_INSERT_ID();
    
    -- Show the archer's class based on age and gender
    SELECT c.ClassID, c.ClassName
    FROM Class c
    JOIN AgeGroup ag ON c.AgeGroupID = ag.AgeGroupID
    WHERE c.Gender = p_Gender
      AND (YEAR(CURDATE()) - YEAR(p_DateOfBirth)) BETWEEN IFNULL(ag.MinAge, 0) AND IFNULL(ag.MaxAge, 999);
END //
DELIMITER ;

-- ======================================================
-- USE CASE 6: Approve Practice Scores
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspApproveScore(
    IN p_StagedScoreID INT,
    IN p_RecorderArcherID INT,
    OUT p_ScoreID INT
)
BEGIN
    DECLARE v_ArcherID INT;
    DECLARE v_RoundID INT;
    DECLARE v_EquipmentTypeID INT;
    DECLARE v_Date DATE;
    DECLARE v_TotalScore INT;
    DECLARE v_IsRecorder BOOLEAN DEFAULT FALSE;
    
    -- Check if the archer has recorder privileges
    SELECT IsRecorder INTO v_IsRecorder
    FROM AppUser
    WHERE ArcherID = p_RecorderArcherID
    LIMIT 1;
    
    -- Only proceed if the archer is a recorder
    IF v_IsRecorder = TRUE THEN
        -- Start transaction
        START TRANSACTION;
        
        -- Get staged score details
        SELECT ArcherID, RoundID, EquipmentTypeID, Date, TotalScore
        INTO v_ArcherID, v_RoundID, v_EquipmentTypeID, v_Date, v_TotalScore
        FROM StagedScore
        WHERE StagedScoreID = p_StagedScoreID;
        
        -- Insert into Score table
        INSERT INTO Score (ArcherID, RoundID, EquipmentTypeID, Date, TotalScore, IsApproved, IsCompetition, ApprovedBy)
        VALUES (v_ArcherID, v_RoundID, v_EquipmentTypeID, v_Date, v_TotalScore, TRUE, FALSE, p_RecorderArcherID);
        
        -- Get the new Score ID
        SET p_ScoreID = LAST_INSERT_ID();
        
        -- Delete from StagedScore table
        DELETE FROM StagedScore
        WHERE StagedScoreID = p_StagedScoreID;
        
        -- Commit transaction
        COMMIT;
    ELSE
        -- Not a recorder, return 0 to indicate failure
        SET p_ScoreID = 0;
    END IF;
END //
DELIMITER ;

-- ======================================================
-- USE CASE 7: Manage Competitions
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspCreateCompetition(
    IN p_CompetitionName VARCHAR(100),
    IN p_Date DATE,
    IN p_IsChampionship BOOLEAN,
    IN p_Description VARCHAR(255),
    OUT p_CompetitionID INT
)
BEGIN
    -- Create a new competition
    INSERT INTO Competition (CompetitionName, Date, IsChampionship, Description)
    VALUES (p_CompetitionName, p_Date, p_IsChampionship, p_Description);
    
    -- Return the new competition ID
    SET p_CompetitionID = LAST_INSERT_ID();
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE uspLinkScoreToCompetition(
    IN p_CompetitionID INT,
    IN p_ScoreID INT
)
BEGIN
    -- Start transaction
    START TRANSACTION;
    
    -- Link the score to the competition
    INSERT INTO CompetitionScore (CompetitionID, ScoreID)
    VALUES (p_CompetitionID, p_ScoreID);
    
    -- Mark the score as a competition score
    UPDATE Score
    SET IsCompetition = TRUE
    WHERE ScoreID = p_ScoreID;
    
    -- Commit transaction
    COMMIT;
END //
DELIMITER ;

-- ======================================================
-- USE CASE 8: Generate Competition Results (Modified)
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspGenerateCompetitionResults(
    IN p_CompetitionID INT
)
BEGIN
    -- Generate competition results with ranking and competition details in a single result set
    SELECT 
           c.CompetitionID, 
           c.CompetitionName,
           c.Date,
           IF(c.IsChampionship, 'Yes', 'No') AS IsChampionship,
           c.Description,
           base.Category,
           base.ArcherName,
           base.RoundName,
           base.TotalScore,
           base.PossibleScore,
           base.ScorePercentage,
           (SELECT COUNT(*) + 1 
            FROM (
              SELECT cs.CompetitionID,
                     CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName,
                     cls.ClassName, 
                     et.Name AS EquipmentType,
                     CONCAT(cls.ClassName, ' ', et.Name) AS Category,
                     r.RoundName, 
                     s.TotalScore,
                     r.PossibleScore,
                     ROUND((s.TotalScore / r.PossibleScore * 100), 2) AS ScorePercentage
              FROM CompetitionScore cs
              JOIN Score s ON cs.ScoreID = s.ScoreID
              JOIN Archer a ON s.ArcherID = a.ArcherID
              JOIN Round r ON s.RoundID = r.RoundID
              JOIN EquipmentType et ON s.EquipmentTypeID = et.EquipmentTypeID
              JOIN Class cls ON (
                  a.Gender = cls.Gender AND
                  (SELECT ag.AgeGroupID 
                   FROM AgeGroup ag 
                   WHERE (YEAR(CURDATE()) - YEAR(a.DateOfBirth)) BETWEEN IFNULL(ag.MinAge, 0) AND IFNULL(ag.MaxAge, 999)
                   LIMIT 1) = cls.AgeGroupID
              )
              WHERE cs.CompetitionID = p_CompetitionID
            ) AS sub
            WHERE sub.Category = base.Category 
              AND sub.ScorePercentage > base.ScorePercentage
           ) AS Ranking
    FROM Competition c
    JOIN (
      SELECT cs.CompetitionID,
             CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName,
             cls.ClassName, 
             et.Name AS EquipmentType,
             CONCAT(cls.ClassName, ' ', et.Name) AS Category,
             r.RoundName, 
             s.TotalScore,
             r.PossibleScore,
             ROUND((s.TotalScore / r.PossibleScore * 100), 2) AS ScorePercentage
      FROM CompetitionScore cs
      JOIN Score s ON cs.ScoreID = s.ScoreID
      JOIN Archer a ON s.ArcherID = a.ArcherID
      JOIN Round r ON s.RoundID = r.RoundID
      JOIN EquipmentType et ON s.EquipmentTypeID = et.EquipmentTypeID
      JOIN Class cls ON (
          a.Gender = cls.Gender AND
          (SELECT ag.AgeGroupID 
           FROM AgeGroup ag 
           WHERE (YEAR(CURDATE()) - YEAR(a.DateOfBirth)) BETWEEN IFNULL(ag.MinAge, 0) AND IFNULL(ag.MaxAge, 999)
           LIMIT 1) = cls.AgeGroupID
      )
      WHERE cs.CompetitionID = p_CompetitionID
    ) AS base ON c.CompetitionID = base.CompetitionID
    WHERE c.CompetitionID = p_CompetitionID
    ORDER BY base.Category, base.ScorePercentage DESC;
END //
DELIMITER ;

-- ======================================================
-- USE CASE 9: User Management (Admin Features)
-- ======================================================

DELIMITER //
CREATE PROCEDURE uspGetAllUsers()
BEGIN
    -- Return all user accounts with archer information
    SELECT u.UserID, u.ArcherID, u.Username, 
           CONCAT(a.FirstName, ' ', a.LastName) AS ArcherName,
           a.DateOfBirth, a.Gender, u.IsRecorder, u.IsAdmin
    FROM AppUser u
    JOIN Archer a ON u.ArcherID = a.ArcherID
    ORDER BY u.UserID;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE uspGetArchersWithoutAccounts()
BEGIN
    -- Find archers who don't have user accounts
    SELECT a.ArcherID, a.FirstName, a.LastName, a.DateOfBirth, a.Gender
    FROM Archer a
    LEFT JOIN AppUser u ON a.ArcherID = u.ArcherID
    WHERE u.UserID IS NULL AND a.IsActive = TRUE
    ORDER BY a.ArcherID;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE uspManageUserAccount(
    IN p_Action VARCHAR(10),
    IN p_UserID INT,
    IN p_ArcherID INT,
    IN p_Username VARCHAR(50),
    IN p_PasswordHash VARCHAR(255),
    IN p_IsRecorder BOOLEAN,
    OUT p_ResultID INT,
    OUT p_Message VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_ResultID = 0;
        SET p_Message = 'Database error occurred';
    END;
    
    START TRANSACTION;
    
    -- Default values
    SET p_ResultID = 0;
    SET p_Message = '';
    
    CASE p_Action
        WHEN 'CREATE' THEN
            -- Check if archer exists
            IF NOT EXISTS (SELECT 1 FROM Archer WHERE ArcherID = p_ArcherID) THEN
                SET p_Message = 'Archer does not exist';
                ROLLBACK;
            -- Check if archer already has an account
            ELSEIF EXISTS (SELECT 1 FROM AppUser WHERE ArcherID = p_ArcherID) THEN
                SET p_Message = 'Archer already has an account';
                ROLLBACK;
            -- Check if username is already taken
            ELSEIF EXISTS (SELECT 1 FROM AppUser WHERE Username = p_Username) THEN
                SET p_Message = 'Username already exists';
                ROLLBACK;
            ELSE
                -- Create new user account
                INSERT INTO AppUser(ArcherID, Username, PasswordHash, IsRecorder, IsAdmin)
                VALUES(p_ArcherID, p_Username, p_PasswordHash, p_IsRecorder, FALSE);
                
                SET p_ResultID = LAST_INSERT_ID();
                SET p_Message = 'User account created successfully';
                COMMIT;
            END IF;
            
        WHEN 'DELETE' THEN
            -- Check if user exists
            IF NOT EXISTS (SELECT 1 FROM AppUser WHERE UserID = p_UserID) THEN
                SET p_Message = 'User does not exist';
                ROLLBACK;
            ELSE
                -- Delete user account
                DELETE FROM AppUser WHERE UserID = p_UserID;
                
                SET p_ResultID = p_UserID;
                SET p_Message = 'User account deleted successfully';
                COMMIT;
            END IF;
            
        WHEN 'RESET' THEN
            -- Check if user exists
            IF NOT EXISTS (SELECT 1 FROM AppUser WHERE UserID = p_UserID) THEN
                SET p_Message = 'User does not exist';
                ROLLBACK;
            ELSE
                -- Reset password
                UPDATE AppUser
                SET PasswordHash = p_PasswordHash
                WHERE UserID = p_UserID;
                
                SET p_ResultID = p_UserID;
                SET p_Message = 'Password reset successfully';
                COMMIT;
            END IF;
            
        ELSE
            SET p_Message = 'Invalid action specified';
            ROLLBACK;
    END CASE;
    
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE uspUpdateRecorderPrivilege(
    IN p_UserID INT,
    IN p_IsRecorder BOOLEAN,
    OUT p_Success BOOLEAN,
    OUT p_Message VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_Success = FALSE;
        SET p_Message = 'Database error occurred';
    END;
    
    -- Check if user exists
    IF NOT EXISTS (SELECT 1 FROM AppUser WHERE UserID = p_UserID) THEN
        SET p_Success = FALSE;
        SET p_Message = 'User does not exist';
    ELSE
        -- Update recorder status
        UPDATE AppUser
        SET IsRecorder = p_IsRecorder
        WHERE UserID = p_UserID;
        
        SET p_Success = TRUE;
        IF p_IsRecorder = TRUE THEN
            SET p_Message = 'Recorder privilege granted successfully';
        ELSE
            SET p_Message = 'Recorder privilege revoked successfully';
        END IF;
    END IF;
END //
DELIMITER ;

-- ======================================================
-- COMPLETED - ALL PROCEDURES AND INDEXES CREATED
-- ======================================================