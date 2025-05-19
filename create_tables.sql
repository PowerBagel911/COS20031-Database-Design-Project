CREATE TABLE EquipmentType (
    EquipmentTypeID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(50) NOT NULL UNIQUE,
    Description VARCHAR(255)
);

CREATE TABLE AgeGroup (
    AgeGroupID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(50) NOT NULL UNIQUE,
    MinAge INT,
    MaxAge INT
);

CREATE TABLE Class (
    ClassID INT PRIMARY KEY AUTO_INCREMENT,
    AgeGroupID INT,
    Gender CHAR(1) NOT NULL,
    ClassName VARCHAR(50) NOT NULL UNIQUE,
    FOREIGN KEY (AgeGroupID) REFERENCES AgeGroup(AgeGroupID)
);

CREATE TABLE Archer (
    ArcherID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    DateOfBirth DATE NOT NULL,
    Gender CHAR(1) NOT NULL,
    DefaultEquipmentTypeID INT,
    IsActive BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (DefaultEquipmentTypeID) REFERENCES EquipmentType(EquipmentTypeID)
);

CREATE TABLE TargetFace (
    TargetFaceID INT PRIMARY KEY AUTO_INCREMENT,
    Size INT NOT NULL,
    Description VARCHAR(255)
);

CREATE TABLE Round (
    RoundID INT PRIMARY KEY AUTO_INCREMENT,
    RoundName VARCHAR(50) NOT NULL UNIQUE,
    TotalArrows INT NOT NULL,
    PossibleScore INT NOT NULL,
    Description VARCHAR(255)
);

-- Renamed "Range" to "RoundRange" to avoid reserved word issues
CREATE TABLE RoundRange (
    RoundRangeID INT PRIMARY KEY AUTO_INCREMENT,
    RoundID INT NOT NULL,
    RangeSequence INT NOT NULL,
    Distance INT NOT NULL,
    NumberOfEnds INT NOT NULL,
    TargetFaceID INT NOT NULL,
    ArrowsPerEnd INT NOT NULL DEFAULT 6,
    FOREIGN KEY (RoundID) REFERENCES Round(RoundID),
    FOREIGN KEY (TargetFaceID) REFERENCES TargetFace(TargetFaceID),
    UNIQUE (RoundID, RangeSequence)
);

CREATE TABLE EquivalentRound (
    EquivalentRoundID INT PRIMARY KEY AUTO_INCREMENT,
    BaseRoundID INT NOT NULL,
    ClassID INT NOT NULL,
    EquipmentTypeID INT NOT NULL,
    EquivalentRoundRefID INT NOT NULL,
    EffectiveDate DATE NOT NULL,
    ExpiryDate DATE,
    FOREIGN KEY (BaseRoundID) REFERENCES Round(RoundID),
    FOREIGN KEY (ClassID) REFERENCES Class(ClassID),
    FOREIGN KEY (EquipmentTypeID) REFERENCES EquipmentType(EquipmentTypeID),
    FOREIGN KEY (EquivalentRoundRefID) REFERENCES Round(RoundID)
);

CREATE TABLE Score (
    ScoreID INT PRIMARY KEY AUTO_INCREMENT,
    ArcherID INT NOT NULL,
    RoundID INT NOT NULL,
    EquipmentTypeID INT NOT NULL,
    Date DATE NOT NULL,
    TotalScore INT NOT NULL,
    IsApproved BOOLEAN DEFAULT FALSE,
    IsCompetition BOOLEAN DEFAULT FALSE,
    ApprovedBy INT,
    FOREIGN KEY (ArcherID) REFERENCES Archer(ArcherID),
    FOREIGN KEY (RoundID) REFERENCES Round(RoundID),
    FOREIGN KEY (EquipmentTypeID) REFERENCES EquipmentType(EquipmentTypeID),
    FOREIGN KEY (ApprovedBy) REFERENCES Archer(ArcherID)
);

CREATE TABLE StagedScore (
    StagedScoreID INT PRIMARY KEY AUTO_INCREMENT,
    ArcherID INT NOT NULL,
    RoundID INT NOT NULL,
    EquipmentTypeID INT NOT NULL,
    Date DATE NOT NULL,
    TotalScore INT NOT NULL,
    SubmissionDate DATETIME NOT NULL,
    FOREIGN KEY (ArcherID) REFERENCES Archer(ArcherID),
    FOREIGN KEY (RoundID) REFERENCES Round(RoundID),
    FOREIGN KEY (EquipmentTypeID) REFERENCES EquipmentType(EquipmentTypeID)
);

CREATE TABLE Competition (
    CompetitionID INT PRIMARY KEY AUTO_INCREMENT,
    CompetitionName VARCHAR(100) NOT NULL,
    Date DATE NOT NULL,
    IsChampionship BOOLEAN DEFAULT FALSE,
    Description VARCHAR(255)
);

CREATE TABLE CompetitionScore (
    CompetitionID INT NOT NULL,
    ScoreID INT NOT NULL,
    PRIMARY KEY (CompetitionID, ScoreID),
    FOREIGN KEY (CompetitionID) REFERENCES Competition(CompetitionID),
    FOREIGN KEY (ScoreID) REFERENCES Score(ScoreID)
);

CREATE TABLE End (
    EndID INT PRIMARY KEY AUTO_INCREMENT,
    ScoreID INT NOT NULL,
    RangeSequence INT NOT NULL,
    EndSequence INT NOT NULL,
    TotalEndScore INT NOT NULL,
    FOREIGN KEY (ScoreID) REFERENCES Score(ScoreID),
    UNIQUE (ScoreID, RangeSequence, EndSequence)
);

CREATE TABLE Arrow (
    ArrowID INT PRIMARY KEY AUTO_INCREMENT,
    EndID INT NOT NULL,
    ArrowScore INT NOT NULL,
    ArrowSequence INT NOT NULL,
    FOREIGN KEY (EndID) REFERENCES End(EndID),
    UNIQUE (EndID, ArrowSequence)
);

-- Renamed "User" to "AppUser" to avoid reserved word issues
CREATE TABLE AppUser (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    ArcherID INT NOT NULL,
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    IsRecorder BOOLEAN DEFAULT FALSE,
    IsAdmin BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (ArcherID) REFERENCES Archer(ArcherID)
);

CREATE TABLE SecurityLog (
    LogID INT PRIMARY KEY AUTO_INCREMENT,
    EventTime DATETIME NOT NULL,
    UserID INT,
    ArcherID INT,
    IPAddress VARCHAR(45),
    EventType VARCHAR(50) NOT NULL,
    Description TEXT,
    Severity VARCHAR(20) NOT NULL,
    ActionURL VARCHAR(255),
    RequestDetails TEXT,
    IsReviewed BOOLEAN DEFAULT FALSE,
    ReviewedBy INT,
    ReviewedAt DATETIME,
    FOREIGN KEY (UserID) REFERENCES AppUser(UserID),
    FOREIGN KEY (ArcherID) REFERENCES Archer(ArcherID),
    FOREIGN KEY (ReviewedBy) REFERENCES AppUser(UserID)
);

CREATE INDEX idx_securitylog_eventtime ON SecurityLog(EventTime);
CREATE INDEX idx_securitylog_userid ON SecurityLog(UserID);
CREATE INDEX idx_securitylog_eventtype ON SecurityLog(EventType);
CREATE INDEX idx_securitylog_severity ON SecurityLog(Severity);
CREATE INDEX idx_securitylog_isreviewed ON SecurityLog(IsReviewed);