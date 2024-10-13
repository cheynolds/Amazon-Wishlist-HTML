let currentPage = 1;
let isInStockOnly = false;
let isInitialRandomizedProductsLoaded = false; // Ensure that random products are loaded once

// Infinite Scroll Function
function attachInfiniteScroll(loadMoreCallback) {
  let loading = false;

  window.addEventListener("scroll", function () {
    const scrollPosition = window.innerHeight + window.scrollY;
    const documentHeight = document.body.offsetHeight;

    if (scrollPosition >= documentHeight - 200 && !loading) {
      loading = true;
      loadMoreCallback().finally(() => {
        loading = false; // Reset loading state after fetching
      });
    }
  });
}

// Function to load more products
// Infinite scroll logic
function loadMoreProducts() {
  if (!isInitialRandomizedProductsLoaded) {
    isInitialRandomizedProductsLoaded = true; // Set flag to true after initial random load
  }

  const url = `/products?page=${currentPage}&in_stock=${isInStockOnly ? 1 : 0}`;

  return fetch(url, {
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((response) => response.json())
    .then((data) => {
      const productGrid = document.getElementById("product-grid");
      if (!productGrid) {
        console.error("product-grid element not found.");
        return;
      }

      // Append new products to the grid
      data.forEach((product) => {
        const productDiv = document.createElement("div");
        productDiv.classList.add("product");
        productDiv.setAttribute("data-stock-status", product.stock_status);
        productDiv.innerHTML = `
                  <img src="${product.image_url}" alt="${product.title}">
                  <h3><a href="/product/${product.asin}">${
          product.title
        }</a></h3>
                  <p><strong>Price:</strong> $${product.price}</p>
                  <p><strong>Price Added:</strong> $${product.price_added}</p>
                  <p><strong>Last Price Change:</strong> $${
                    product.last_pricechange
                  } (${product.last_pricechange_percent}%)</p>
                  <p><strong>Status:</strong> ${
                    product.stock_status === "In Stock"
                      ? "<span>In Stock</span>"
                      : "<span>Out of Stock</span>"
                  }</p>
                  <p><strong>Reviews:</strong> ${product.reviews || "N/A"}</p>
                  <p><strong>Rating:</strong> ${
                    product.stars || "N/A"
                  } stars</p>
                  <p><strong>Pattern:</strong> ${product.pattern || "N/A"}</p>
                  <p><strong>Style:</strong> ${product.style || "N/A"}</p>
                  <p><strong>Wishlist:</strong> ${
                    product.wishlist_name || "N/A"
                  }</p>
                  <p><strong>Date Added:</strong> ${
                    product.date_added || "N/A"
                  }</p>
                  <p><strong>Last Price Check:</strong> ${
                    product.last_checkdate || "N/A"
                  }</p>
                  <div class="product-button-container">
                      <a href="${
                        product.product_link
                      }" target="_blank">View on Amazon</a>
                      ${
                        product.affiliate_link
                          ? `<a href="${product.affiliate_link}" target="_blank">Affiliate Link</a>`
                          : ""
                      }
                  </div>`;
        productGrid.appendChild(productDiv);
      });
    });
}

// Toggle In-Stock Function
function toggleInStock(button, seed) {
  const urlParams = new URLSearchParams(window.location.search);
  let inStock = urlParams.get("in_stock");
  const page = urlParams.get("page") || 1;

  // Toggle the in-stock flag
  inStock = inStock === "1" ? "0" : "1";

  // Update button state visually
  updateButtonState(button, inStock === "1");

  // Construct the new URL with the preserved seed and updated in-stock filter
  const newUrl = `/products?seed=${seed}&in_stock=${inStock}&page=${page}`;

  // Redirect to the new URL to apply the changes
  window.location.href = newUrl;
}

// Function to update the button text and color based on the in-stock filter state
function updateButtonState(button, isInStock) {
  if (isInStock) {
    button.textContent = "Show All Products";
    button.style.backgroundColor = "#4CAF50"; // Green color when showing in-stock items
  } else {
    button.textContent = "Show In Stock Only";
    button.style.backgroundColor = "#f44336"; // Red color when showing all items
  }
}
// Home Button Functionality (modified to retain seed if available)
function goToHome() {
  // Redirect to the products page with no parameters to trigger a fresh product list
  window.location.href = "/products";
}

// Go to Top Button Functionality
document.addEventListener("DOMContentLoaded", function () {
  window.onscroll = function () {
    const scrollTopBtn = document.getElementById("scrollTopBtn");
    if (
      document.body.scrollTop > 300 ||
      document.documentElement.scrollTop > 300
    ) {
      scrollTopBtn.style.display = "block"; // Show the button
    } else {
      scrollTopBtn.style.display = "none"; // Hide the button
    }
  };

  window.scrollToTop = function () {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Attach infinite scroll functionality
  attachInfiniteScroll(() => {
    currentPage += 1;
    return loadMoreProducts();
  });

  // Load initial set of products
  loadMoreProducts();
});
