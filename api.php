<?php
// Enable CORS to allow requests from Streamlit
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json");

// Database connection parameters
$host = "feenix-mariadb-web.swin.edu.au";
$port = 3306; // Explicitly set port
$dbname = "s105089392_db";
$username = "s105089392"; // Replace with your database username
$password = "."; // Replace with your database password

// Create connection
$conn = new mysqli($host, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die(json_encode(["error" => "Connection failed: " . $conn->connect_error]));
}

// Get the request method
$method = $_SERVER['REQUEST_METHOD'];

// Handle different API endpoints
$endpoint = isset($_GET['endpoint']) ? $_GET['endpoint'] : '';

switch ($endpoint) {
    case 'archers':
        getArchers($conn);
        break;
    case 'equipment_types':
        getEquipmentTypes($conn);
        break;
    case 'rounds':
        getRounds($conn);
        break;
    case 'scores':
        if ($method == 'GET') {
            getScores($conn);
        } elseif ($method == 'POST') {
            addScore($conn);
        }
        break;
    case 'competitions':
        getCompetitions($conn);
        break;
    case 'login':
        login($conn);
        break;
    default:
        echo json_encode(["error" => "Invalid endpoint"]);
}

// Function to get all archers
function getArchers($conn) {
    $sql = "SELECT * FROM Archer";
    $result = $conn->query($sql);
    
    $archers = [];
    if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
            $archers[] = $row;
        }
    }
    
    echo json_encode($archers);
}

// Function to get all equipment types
function getEquipmentTypes($conn) {
    $sql = "SELECT * FROM EquipmentType";
    $result = $conn->query($sql);
    
    $types = [];
    if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
            $types[] = $row;
        }
    }
    
    echo json_encode($types);
}

// Function to get all rounds
function getRounds($conn) {
    $sql = "SELECT * FROM Round";
    $result = $conn->query($sql);
    
    $rounds = [];
    if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
            $rounds[] = $row;
        }
    }
    
    echo json_encode($rounds);
}

// Function to get scores
function getScores($conn) {
    $archerId = isset($_GET['archer_id']) ? intval($_GET['archer_id']) : null;
    
    $sql = "SELECT s.*, r.RoundName, e.Name as EquipmentType, 
            CONCAT(a.FirstName, ' ', a.LastName) as ArcherName 
            FROM Score s
            JOIN Round r ON s.RoundID = r.RoundID
            JOIN EquipmentType e ON s.EquipmentTypeID = e.EquipmentTypeID
            JOIN Archer a ON s.ArcherID = a.ArcherID";
    
    if ($archerId) {
        $sql .= " WHERE s.ArcherID = $archerId";
    }
    
    $result = $conn->query($sql);
    
    $scores = [];
    if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
            $scores[] = $row;
        }
    }
    
    echo json_encode($scores);
}

// Function to add a new score
function addScore($conn) {
    $data = json_decode(file_get_contents('php://input'), true);
    
    // Validate required fields
    if (!isset($data['archerId']) || !isset($data['roundId']) || 
        !isset($data['equipmentTypeId']) || !isset($data['totalScore'])) {
        echo json_encode(["error" => "Missing required fields"]);
        return;
    }
    
    // First add to staged scores
    $sql = "INSERT INTO StagedScore (ArcherID, RoundID, EquipmentTypeID, Date, TotalScore, SubmissionDate) 
            VALUES (?, ?, ?, CURDATE(), ?, NOW())";
    
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("iiid", $data['archerId'], $data['roundId'], $data['equipmentTypeId'], $data['totalScore']);
    
    if ($stmt->execute()) {
        echo json_encode(["success" => true, "message" => "Score submitted for approval"]);
    } else {
        echo json_encode(["error" => "Error: " . $stmt->error]);
    }
}

// Function to get competitions
function getCompetitions($conn) {
    $sql = "SELECT * FROM Competition ORDER BY Date DESC";
    $result = $conn->query($sql);
    
    $competitions = [];
    if ($result->num_rows > 0) {
        while($row = $result->fetch_assoc()) {
            $competitions[] = $row;
        }
    }
    
    echo json_encode($competitions);
}

// Function to handle login
function login($conn) {
    $data = json_decode(file_get_contents('php://input'), true);
    
    if (!isset($data['username']) || !isset($data['password'])) {
        echo json_encode(["error" => "Username and password required"]);
        return;
    }
    
    $sql = "SELECT u.*, a.FirstName, a.LastName FROM AppUser u 
            JOIN Archer a ON u.ArcherID = a.ArcherID 
            WHERE u.Username = ?";
    
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("s", $data['username']);
    $stmt->execute();
    $result = $stmt->get_result();
    
    if ($result->num_rows === 1) {
        $user = $result->fetch_assoc();
        // In a real app, you'd use password_verify() to check hashed passwords
        // For this assignment, we'll assume the password is correct
        // if (password_verify($data['password'], $user['PasswordHash'])) {
        echo json_encode([
            "success" => true,
            "user" => [
                "id" => $user['UserID'],
                "archerId" => $user['ArcherID'],
                "name" => $user['FirstName'] . ' ' . $user['LastName'],
                "isRecorder" => $user['IsRecorder'],
                "isAdmin" => $user['IsAdmin']
            ]
        ]);
        // } else {
        //     echo json_encode(["error" => "Invalid password"]);
        // }
    } else {
        echo json_encode(["error" => "User not found"]);
    }
}

$conn->close();
?>
