<?php
// SQL Injection Vulnerability
$username = $_GET['username'];
$password = $_GET['password'];

$query = "SELECT * FROM users WHERE username='$username' AND password='$password'";
$result = mysqli_query($conn, $query);

// Code Injection Vulnerability
$userInput = $_GET['page'];
include($userInput . '.php');

// Eval Injection
$callback = $_GET['callback'];
eval($callback);

// Command Injection
$command = $_GET['cmd'];
system($command);

// File Inclusion
$file = $_GET['file'];
include($file);

// Unserialize Vulnerability
$cookie = $_COOKIE['session'];
$data = unserialize($cookie);

// File Upload Vulnerability
if ($_FILES['upload']['size'] > 0) {
    $target = "uploads/" . $_FILES['upload']['name'];
    move_uploaded_file($_FILES['upload']['tmp_name'], $target);
}
?>
