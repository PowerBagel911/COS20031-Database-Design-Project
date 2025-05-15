<?php
// Enable error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Database connection parameters
$host = "feenix-mariadb-web.swin.edu.au";
$port = 3306;  // Standard MySQL/MariaDB port
$dbname = "s105089392_db";
$username = "s105089392";
$password = "ductri05";

try {
    echo "Attempting to connect to database...\n";
    echo "Using host: $host, port: $port, database: $dbname\n";
    
    // Try to establish connection
    $conn = new mysqli($host, $username, $password, $dbname, $port);

    // Check connection
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error . "\n");
    }
    
    echo "Connection successful! Connected to database: " . $dbname . "\n";
    
    // Try a simple query
    $result = $conn->query("SELECT 1");
    if ($result) {
        echo "Test query successful!\n";
    }
    
    // Close the connection
    $conn->close();
    echo "Connection closed.\n";
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
    echo "Error Code: " . $e->getCode() . "\n";
}
?> 