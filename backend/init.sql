CREATE DATABASE IF NOT EXISTS Holmes;
USE Holmes;

-- Create the user table first, as the scan table will reference it
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create the scan table with a direct one-to-many relationship to the user table
CREATE TABLE IF NOT EXISTS scans (
    scan_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(50),
    email LONGTEXT,
    is_phishing BOOLEAN,
    risk_level ENUM('low', 'medium', 'high'),
    explanation TEXT,
    date DATETIME,
    
    -- Establish the foreign key relationship
    CONSTRAINT fk_users_scan 
        FOREIGN KEY (user_id) 
        REFERENCES users(user_id) 
        ON DELETE CASCADE
);

DROP PROCEDURE IF EXISTS RegisterUser;

DELIMITER //

CREATE PROCEDURE RegisterUser(
    IN p_email VARCHAR(100),
    IN p_username VARCHAR(50),
    IN p_password VARCHAR(255),
    OUT p_new_user_id INT
)
BEGIN
    -- Insert the new user details into the users table
    INSERT INTO users (email, username, password)
    VALUES (p_email, p_username, p_password);
    
    -- Capture the newly generated auto-increment ID and assign it to our OUT parameter
    SET p_new_user_id = LAST_INSERT_ID();
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS GetUserByEmail;

DELIMITER //

CREATE PROCEDURE GetUserByEmail(
    IN p_email VARCHAR(100)
)
BEGIN
    -- This will return a result set containing the user_id and password
    SELECT user_id, password 
    FROM users 
    WHERE email = p_email;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS GetUserById;

DELIMITER //

CREATE PROCEDURE GetUserById(
	IN p_user_id INT
)
BEGIN
    SELECT user_id, email, username 
    FROM users 
    WHERE user_id = p_user_id;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS GetUserScansSummary;

DELIMITER //

CREATE PROCEDURE GetUserScansSummary(
    IN p_user_id INT
)
BEGIN
    SELECT scan_id, title, is_phishing, risk_level, date 
    FROM scans 
    WHERE user_id = p_user_id
    ORDER BY date DESC; -- Orders them from newest to oldest!
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS GetScanDetails;

DELIMITER //

CREATE PROCEDURE GetScanDetails(
    IN p_scan_id INT,
    IN p_user_id INT
)
BEGIN
    -- Select all columns, strictly enforcing ownership
    SELECT * FROM scans 
    WHERE scan_id = p_scan_id AND user_id = p_user_id;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS InsertNewScan;

DELIMITER //

CREATE PROCEDURE InsertNewScan(
    IN p_user_id INT,
    IN p_title VARCHAR(50),
    IN p_email LONGTEXT,
    IN p_is_phishing BOOLEAN,
    IN p_risk_level ENUM('low', 'medium', 'high'),
    IN p_explanation TEXT,
    IN p_date DATETIME
)
BEGIN
    -- 1. Insert the new record
    INSERT INTO scans (user_id, title, email, is_phishing, risk_level, explanation, date)
    VALUES (p_user_id, p_title, p_email, p_is_phishing, p_risk_level, p_explanation, p_date);
    
    -- 2. Return the newly generated auto-increment ID
    SELECT LAST_INSERT_ID() AS new_scan_id;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS SearchScans;

DELIMITER //

CREATE PROCEDURE SearchScans(
    IN p_user_id INT,
    IN p_search_term VARCHAR(255)
)
BEGIN
    -- Fetch only the necessary summary columns!
    SELECT scan_id, title, is_phishing, risk_level, date 
    FROM scans 
    WHERE user_id = p_user_id 
    AND (
        title LIKE CONCAT('%', p_search_term, '%') 
        OR email LIKE CONCAT('%', p_search_term, '%')
    )
    ORDER BY date DESC;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS RenameScan;

DELIMITER //

CREATE PROCEDURE RenameScan(
    IN p_user_id INT,
    IN p_scan_id INT,
    IN p_new_title VARCHAR(50)
)
BEGIN
    UPDATE scans 
    SET title = p_new_title 
    WHERE scan_id = p_scan_id AND user_id = p_user_id;
END //

DELIMITER ;

DROP PROCEDURE IF EXISTS DeleteScan;

DELIMITER //

CREATE PROCEDURE DeleteScan(
    IN p_user_id INT,
    IN p_scan_id INT
)
BEGIN
    DELETE FROM scans 
    WHERE scan_id = p_scan_id AND user_id = p_user_id;
END //

DELIMITER ;