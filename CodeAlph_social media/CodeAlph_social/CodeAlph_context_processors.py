def nav_counts(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'nav_unread_count': request.user.notifications.filter(is_read=False).count(),
        'nav_request_count': request.user.received_follow_requests.count(),
    }
