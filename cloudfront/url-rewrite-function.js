// CloudFront Function to handle clean URLs (remove .html extension)
// This function runs on viewer request
// Note: CloudFront Functions receive URI WITHOUT query parameters
// Query parameters are automatically preserved in request.querystring

function handler(event) {
    var request = event.request;
    var uri = request.uri;
    
    // List of valid routes (without .html extension)
    var validRoutes = [
        '/index',
        '/auth',
        '/reset-password',
        '/dashboard',
        '/gallery',
        '/new-gallery',
        '/client-gallery',
        '/client-dashboard',
        '/profile-settings',
        '/portfolio-settings',
        '/portfolio',
        '/photographers',
        '/pricing',
        '/billing',
        '/contact',
        '/faq',
        '/privacy',
        '/legal-notice',
        '/404'
    ];
    
    // If URI ends with '/', serve index.html
    if (uri.endsWith('/')) {
        request.uri += 'index.html';
        return request;
    }
    
    // If URI has an extension (e.g., .css, .js, .png), serve as-is
    if (uri.includes('.') && !uri.endsWith('.html')) {
        return request;
    }
    
    // If URI is in validRoutes, append '.html'
    // Query parameters in request.querystring are automatically preserved
    if (validRoutes.includes(uri)) {
        request.uri += '.html';
        return request;
    }
    
    // If URI already ends with .html and is valid, serve it
    if (uri.endsWith('.html')) {
        var routeWithoutHtml = uri.substring(0, uri.length - 5);
        if (validRoutes.includes(routeWithoutHtml) || uri === '/index.html') {
            return request;
        }
    }
    
    // For any unrecognized route (invalid URL), redirect to 404
    request.uri = '/404.html';
    return request;
}
