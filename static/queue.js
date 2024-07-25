document.addEventListener("DOMContentLoaded", () => {    
    const queueButton = document.getElementById('queue-btn');
    const searchInput = document.getElementById('search-input');
    const togglePlayButton = document.getElementById('togglePlayBtn')
    const skipButton = document.getElementById('skipBtn')
    const rewindButton = document.getElementById('rewindBtn')
    const refreshButton = document.getElementById('refreshBtn')

    fetchQueueData()
    console.log(togglePlayButton)


    function populateMusicList(queueData) {
        const musicList = document.getElementById('music-list');
        musicList.innerHTML = '';
    
        queueData.forEach(song => {
            const listItem = document.createElement('li');
            listItem.textContent = song;
            musicList.appendChild(listItem);
        });
    }

    function fetchQueueData() {
        fetch('/queue')
            .then(response => response.json())
            .then(data => {
                console.log(data)
                populateMusicList(data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }


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



    queueButton.addEventListener('click', function() {
        const selectedSong = searchInput.value;
        console.log(selectedSong)
        if (selectedSong) {
            fetch('/queue_add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ song: selectedSong })
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

    togglePlayButton.addEventListener('click', function() {
        console.log("play pressed")
        fetch('/queue_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command: "toggle_play" })
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
    });

    skipButton.addEventListener('click', function() {
        fetch('/queue_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command: "skip" })
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
    });

    refreshButton.addEventListener('click', function() {
        fetchQueueData()
    })

    rewindButton.addEventListener('click', function() {
        fetch('/queue_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command: "rewind" })
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
        
    });
});
