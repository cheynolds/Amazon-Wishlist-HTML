let isInStockOnly = false; // Global variable to track if "in stock only" is toggled



// Infinite Scroll Function
function attachInfiniteScroll(loadMoreCallback) {
    let loading = false;

    window.addEventListener('scroll', function() {
        const scrollPosition = window.innerHeight + window.scrollY;
        const documentHeight = document.body.offsetHeight;

        if (scrollPosition >= documentHeight - 200 && !loading) {
            loading = true;

            loadMoreCallback(isInStockOnly) // Pass in the filter state
            .finally(() => {
                loading = false;  // Reset loading state after fetching
            });
        }
    });
}

// Toggle In Stock Function
function toggleInStock() {
    const button = document.getElementById('toggleInStock');
    const products = document.querySelectorAll('.product');
    const isShowingInStock = button.classList.toggle('active');

    // Toggle button text
    button.textContent = isShowingInStock ? "Show All Products" : "Show In Stock Only";

    // Loop through each product and hide/show based on stock status
    products.forEach(product => {
        const stockStatus = product.getAttribute('data-stock-status');
        if (isShowingInStock && stockStatus !== 'In Stock') {
            product.style.display = 'none';  // Hide out of stock
        } else {
            product.style.display = 'block'; // Show all or in stock
        }
    });
}



document.addEventListener('DOMContentLoaded', function() {
    // Show the "Go to Top" button when scrolled down
    window.onscroll = function() {
        const scrollTopBtn = document.getElementById('scrollTopBtn');
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            scrollTopBtn.style.display = 'block';  // Show the button
        } else {
            scrollTopBtn.style.display = 'none';  // Hide the button
        }
    };

    // Function to scroll to the top smoothly
    window.scrollToTop = function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };
});
