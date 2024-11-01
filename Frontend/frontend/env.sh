#!/bin/sh

# Recreate config file
echo "window._env_ = {" > /usr/share/nginx/html/env-config.js

# Add assignment 
echo "  REACT_APP_PDF_TO_CSV_URL: \"$REACT_APP_PDF_TO_CSV_URL\"," >> /usr/share/nginx/html/env-config.js
echo "  REACT_APP_API_URL: \"$REACT_APP_API_URL\"," >> /usr/share/nginx/html/env-config.js

echo "}" >> /usr/share/nginx/html/env-config.js