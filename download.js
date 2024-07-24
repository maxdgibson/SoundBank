document.addEventListener("DOMContentLoaded", () => {
    const downloadButton = document.getElementById('download-btn');
    const searchInput = document.getElementById('search-input');
    console.log("downloadButton")

    // Fetch the CSV file
    fetch('static/TopSongs.csv')
        .then(response => response.text())
        .then(data => {
            const musicData = data.split('\n').map(line => line.trim());
            const datalist = document.getElementById('music-suggestions');
            
            // Populate the datalist with music suggestions
            musicData.forEach(music => {
                const [_, artist, songName, year] = music.split(',');
                if (artist && songName && year) {
                    const option = document.createElement('option');
                    option.value = `${artist} - ${songName} (${year})`;
                    datalist.appendChild(option);
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });

});