document.addEventListener("DOMContentLoaded", () => {
    const downloadButton = document.getElementById('download-btn');
    const searchInput = document.getElementById('search-input');
    const playlistSelect = document.getElementById('playlist-select'); // New line

    // Fetch user-created playlists and populate the dropdown menu
    fetch('/playlists')
        .then(response => response.json())
        .then(playlists => {
            playlists.forEach(playlist => {
                const option = document.createElement('option');
                option.value = playlist;
                option.textContent = playlist;
                playlistSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching playlists:', error);
        });

    // queueButton.addEventListener('click', function() {
    downloadButton.addEventListener('click', function() {
        const selectedSong = searchInput.value;
        const selectedPlaylist = playlistSelect.value; // New line

        if (selectedSong && selectedPlaylist) { // Updated condition
            fetch('/download_add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    playlist: selectedPlaylist, // Updated payload
                    song: selectedSong
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                // Optionally, you can display a success message to the user
            })
            .catch(error => {
                console.error('Error:', error);
                // Optionally, you can display an error message to the user
            });
        }
    });
});