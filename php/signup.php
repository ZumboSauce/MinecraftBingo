<?php
    session_start();
    include __DIR__ . '/config.php';

    error_reporting(E_ALL);
    ini_set('display_errors', '1');
    //TODO ADD ERROR HANDLING
    if (strlen($_POST["user"]) > NAME_LENGTH_MAX){ die("NAMELENERR"); }
    else if ( !ctype_alnum( $_POST["user"] )) { die("NAMEILLEGALCHARERR"); }
    else if ($_POST["pass"] != $_POST["pass-con"]) { die("PASSMATCHERR"); }
    else if ( preg_match('/'.str_replace('\n', '|', file_get_contents(PROFANITY_LIST)).'/gm', $_POST["user"]) ) { die("NAMEILLEGALWORDERR"); }

    $conn = new mysqli(SERVERNAME, USERNAME, PASSWORD, DB);
    if($conn->connect_error) { die("Connection failed: " . $conn->connect_error); }

    $pass = password_hash($_POST["pass"], PASSWORD_BCRYPT);
    $useradd_sql = "INSERT INTO user (name, pass) VALUES (?, ?)";
    $signup_stmt = $conn->prepare($useradd_sql);
    $signup_stmt->bind_param("ss", $_POST["user"], $pass);

    if ($signup_stmt->execute() === TRUE) {
        $_SESSION['user_id'] = $conn->insert_id;
    } else {
        die("NAMEEXISTSERR");
    }