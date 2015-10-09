angular.module('conciergeApp.services', ['ngResource'])
    .factory('Guest', function($resource) {
        return $resource('/api/guests/:id/');
    })
    .factory('Message', function($resource) {
        return $resource('/api/messages/:id/', null,
            {
                'update': {method: 'PATCH'}
            });
    })
    .factory('GuestMessages', function($resource) {
        return $resource('/api/guest-messages/:id/');
    })
    .factory('Reply', ['$resource', function($resource) {
        return $resource('/api/reply/:id/', null,
            {
                'update': {method: 'PATCH'}
            });
    }])
    .factory('ReplyHotelLetters', function($resource) {
        return $resource('/api/reply/hotel-letters/:id/');
    });