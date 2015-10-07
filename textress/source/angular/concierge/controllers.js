var conciergeControllers = angular.module('conciergeApp.controllers', ['conciergeApp.services']);

conciergeControllers.controller('GuestListCtrl', ['$scope', '$timeout', 'Guest', 'Message',
    function($scope, $timeout, Guest, Message) {
        // live
        $scope.guests = Guest.query();

        // Sorting for List
        $scope.predicate = 'name';
        $scope.reverse = true;
        $scope.order = function(predicate) {
            $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
            $scope.predicate = predicate;
        };

        // GuestListView: Push incoming messsage onto Guest Messages array for all Guests
        var initializing = true;

        $scope.getMessage = function(message) {

            var gm = function(message) {
                // goal: convert to JSON in order to handle
                if (typeof(message) !== "object") {
                    message = JSON.parse(message);
                }

                for (i = 0; i < $scope.guests.length; i++) {
                    if (message.guest == $scope.guests[i].id) {
                        $scope.guest = $scope.guests[i]; // set as local $scope to the Ctrl otherwise
                        // can't access it w/i `Message.get()` below
                        Message.get({
                            id: message.id
                        }, function(response) {
                            // Only append the Message if it belongs to the Guest
                            // $scope.guests[i].messages.unshift(response);
                            $scope.guest.messages.push(response);
                        });
                    }
                }
            }

            if (initializing) {
                $timeout(function() {
                    initializing = false;
                });
            } else {
                gm(message);
            }
        }
    }
]);

// ``Dashboard page``: where new messages should pop via a websocket to dispay to the User
conciergeControllers.controller('GuestMsgPreviewCtrl', ['$scope', '$filter', '$stateParams', '$timeout', 'Message', 'GuestMessages',
    function($scope, $filter, $stateParams, $timeout, Message, GuestMessages) {

        $scope.guests = GuestMessages.query();

        // Append Last Message object to each Guest in Array
        // LastMsg has: text, time, read/unread status

        // GuestListView: Push incoming messsage onto Guest Messages array for all Guests
        var initializing = true;

        $scope.getMessage = function(message) {

            var gm = function(message) {
                // goal: convert to JSON in order to handle
                if (typeof(message) !== "object") {
                    message = JSON.parse(message);
                }

                for (i = 0; i < $scope.guests.length; i++) {
                    if (message.guest == $scope.guests[i].id) {
                        $scope.guest = $scope.guests[i]; // set as local $scope to the Ctrl otherwise
                        // can't access it w/i `Message.get()` below
                        Message.get({
                            id: message.id
                        }, function(response) {
                            // Only append the Message if it belongs to the Guest
                            // $scope.guests[i].messages.unshift(response);
                            $scope.guest.messages.push(response);
                        });
                    }
                }
            }

            if (initializing) {
                $timeout(function() {
                    initializing = false;
                });
            } else {
                gm(message);
            }
        }
    }
]);

// Use for single GuestDetail page w/ SMS messages. Send/Receive SMS
// GuestUser = Guest
conciergeControllers.controller('GuestMessageCtrl', ['$scope', '$stateParams', '$timeout', 'Message', 'GuestMessages', 'GuestUser', 'CurrentUser',
    function($scope, $stateParams, $timeout, Message, GuestMessages, GuestUser, CurrentUser) {
        $scope.messages = {};
        $scope.modal_msg = 0;
        $scope.user_id = CurrentUser.id;

        // Guest (single)
        $scope.getGuest = function(GuestMessages, $stateParams, $scope) {
            GuestMessages.get({
                id: GuestUser.id //$stateParams.guestId
            }, function(response) {
                $scope.guest = response;
                $scope.to = response.phone_number;
                $scope.messages = response.messages;
            });
        }

        // populate initial context without a delay
        $scope.getGuest(GuestMessages, $stateParams, $scope);

        $scope.submitMessage = function(ws4redis, body) {
            $scope.body = null;

            var message = new Message({
                to_ph: $scope.to,
                guest: $scope.guest.id,
                user: $scope.user_id,
                body: body
            });

            // `response` needed to get full object:
            // http://stackoverflow.com/questions/17131643/promise-on-angularjs-resource-save-action
            message.$save(function() {
                $scope.messages.unshift(message);
            })
                .then(function(response) {
                    console.log('typeof:', typeof(response), 'id:', response.id, 'response:', response);
                    console.log('Acutual msg being sent:', JSON.stringify(response));
                    ws4redis.send_message(JSON.stringify(response));
                });
        }

        // set flag to not call gm() on page load using $timeout. So the 
        // previous message isn't added to $scope.messages upon page load
        // ref: http://stackoverflow.com/questions/16947771/how-do-i-ignore-the-initial-load-when-watching-model-changes-in-angularjs
        var initializing = true;

        $scope.getMessage = function(message) {

            var gm = function(message) {
                // `message` is an array when sent from the User/Guest's View.
                // when sitting on another view, and receiving from Redis, it is an object.
                // goal: convert to JSON in order to handle
                console.log('typeof:', typeof(message));
                console.log('message pre-JSON:', message);
                if (typeof(message) !== "object") {
                    message = JSON.parse(message);
                }
                console.log('message post-JSON:', message);
                console.log('typeof:', typeof(message));

                if (message.guest == GuestUser.id) {
                    Message.get({
                        id: message.id
                    }, function(response) {
                        // Message should be marked as 'read=true' at this point because 
                        //  is being rendered in the GuestDetailView to the User
                        response.read = true;
                        response.user = null;
                        Message.update({
                            id: response.id
                        }, response);
                        // Only append the Message if it belongs to the Guest
                        $scope.messages.unshift(response);
                    });
                }
            }

            if (initializing) {
                $timeout(function() {
                    initializing = false;
                });
            } else {
                gm(message);
            }
        }
    }
]);

conciergeControllers.controller('ReplyCtrl', ['$scope', 'Reply',
    function($scope, Reply) {
        // live
        $scope.replies = Reply.query();
    }
]);