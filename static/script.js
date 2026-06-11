async function analyze() {
    const input = document.getElementById("moodInput");
    const mood = input.value.trim();

    if (!mood) {
        showError("Opisz najpierw swój nastrój!");
        return;
    }

    const btn = document.getElementById("analyzeBtn");
    btn.disabled = true;
    hideAll();
    document.getElementById("loader").classList.remove("hidden");

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mood })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || "Coś poszło nie tak.");
            return;
        }

        showResults(data);

    } catch (err) {
        showError("Błąd połączenia z serwerem.");
    } finally {
        document.getElementById("loader").classList.add("hidden");
        btn.disabled = false;
    }
}

function showResults(data) {
    const { mood, spotify, youtube } = data;

    const badge = document.getElementById("moodBadge");
    badge.textContent = `${mood.mood_emoji} ${mood.mood_summary}`;

    // Spotify
    const spotifyEl = document.getElementById("spotifyContent");
    if (spotify && !spotify.error) {
        spotifyEl.innerHTML = `
            ${spotify.image ? `<img class="playlist-img" src="${spotify.image}" alt="${spotify.name}">` : ""}
            <div class="playlist-name">${spotify.name}</div>
            <div class="playlist-meta">przez ${spotify.owner} · ${spotify.tracks} utworów</div>
            <a class="open-btn spotify-btn" href="${spotify.url}" target="_blank">Otwórz w Spotify</a>
        `;
    } else {
        spotifyEl.innerHTML = `<p style="color:var(--muted)">Nie znaleziono playlisty.</p>`;
    }

    // YouTube
    const youtubeEl = document.getElementById("youtubeContent");
    if (youtube && !youtube.error) {
        youtubeEl.innerHTML = `
            <a href="${youtube.url}" target="_blank">
                <img class="video-thumb" src="${youtube.thumbnail}" alt="${youtube.title}">
            </a>
            <div class="video-title">${youtube.title}</div>
            <div class="video-channel">${youtube.channel}</div>
            <a class="open-btn youtube-btn" href="${youtube.url}" target="_blank">Oglądaj na YouTube</a>
        `;
    } else {
        youtubeEl.innerHTML = `<p style="color:var(--muted)">Nie znaleziono filmu.</p>`;
    }

    document.getElementById("results").classList.remove("hidden");
}

function showError(msg) {
    const el = document.getElementById("error");
    el.textContent = msg;
    el.classList.remove("hidden");
}

function hideAll() {
    document.getElementById("results").classList.add("hidden");
    document.getElementById("error").classList.add("hidden");
}

document.getElementById("moodInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        analyze();
    }
});
