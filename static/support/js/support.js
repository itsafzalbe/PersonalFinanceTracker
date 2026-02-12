// Simple Support Button - Auto update unread count
document.addEventListener('DOMContentLoaded', function() {
    const supportBtn = document.getElementById('supportBtn');
    
    if (!supportBtn) return;
    
    function updateUnreadCount() {
        fetch('/support/api/unread/')
            .then(response => response.json())
            .then(data => {
                if (data.unread_count > 0) {
                    supportBtn.classList.add('has-unread');
                    supportBtn.setAttribute('data-unread', data.unread_count);
                } else {
                    supportBtn.classList.remove('has-unread');
                }
            })
            .catch(error => console.error('Error:', error));
    }
    
    // Update on load and every 30 seconds
    updateUnreadCount();
    setInterval(updateUnreadCount, 30000);
});

// Auto-scroll chat to bottom
function scrollChatToBottom() {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Call on page load
window.addEventListener('load', scrollChatToBottom);
