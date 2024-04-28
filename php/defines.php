<?php
define("QUERIES", [
    "check_spot" => function ($args) { return array("user_id" => /*$_SESSION['user_id']*/ 1, "space_number" => $args['space_number']); },
    "request_cards" => function ($args) { return array("user_id" => /*$_SESSION['user_id']*/ 1); },
    "sse_subscribe" => function ($args) { return array("user_id" => /*$_SESSION['user_id']*/ 1, "reconnect" => 1); },
    "check_bingo" => function($args) { return array("user_id" => /*$_SESSION['user_id']*/ 1); }
]);