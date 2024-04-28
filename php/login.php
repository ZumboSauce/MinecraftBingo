<?php
    //TODO ADD ERROR HANDLING
    session_start();
    include __DIR__ . '/config.php';

    $conn = new mysqli(SERVERNAME, USERNAME, PASSWORD, DB);

    if($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    $pass = "";
    $id = null;
    $login_sql = "SELECT pass, id FROM user WHERE name = ?";
    $login_stmt = $conn->prepare($login_sql);
    $login_stmt->bind_param("s", $_POST["user"]);
    $login_stmt->execute();
    $login_stmt->bind_result($pass, $id);
    $login_stmt->fetch();
    $login_stmt->close();
    if(password_verify($_POST["pass"], $pass)) {
        $_SESSION['user_id'] = $id;
    } else {
        die("CREDERR");
    }