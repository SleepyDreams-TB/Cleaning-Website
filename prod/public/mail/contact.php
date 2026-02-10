<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $name = htmlspecialchars(trim($_POST["name"]));
    $email = filter_var(trim($_POST["email"]), FILTER_SANITIZE_EMAIL);
    $message = htmlspecialchars(trim($_POST["message"]));

    if (!$name || !$email || !$message) {
        http_response_code(400);
        echo "All fields are required.";
        exit;
    }

    $to = "tiaanburger1112@gmail.com";
    $subject = "New Booking from $name";
    $body = "Name: $name\nEmail: $email \nMessage:\n$message";
    $headers = "From: $name <$email>";

    if (mail($to, $subject, $body, $headers)) {
        http_response_code(200);
        echo "Thank you! Your message has been sent.";
    } else {
        http_response_code(500);
        echo "Oops! Something went wrong. Please try again.";
    }
} else {
    http_response_code(403);
    echo "There was a problem with your submission.";
}
