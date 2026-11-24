/* Visually Moving — text-only chess visualization flashcards.
   No board diagrams. Three exercise types:
   1. "how-would-you-play" — position + prompt → find the move
   2. "determine-positions" — position + continuation → where do pieces end up
   3. "play-out-the-game"  — full game moves → find the winning move

   Each deck loads its JSON from /data/<category>.json */
(function(){
  "use strict";

  /* ── data base URL ── */
  function dataBaseUrl(){
    var scripts = document.getElementsByTagName("script");
    for (var i = 0; i < scripts.length; i++){
      var src = scripts[i].src || "";
      if (src.indexOf("exercise.js") !== -1){
        return src.replace(/js\/exercise\.js.*$/, "data/");
      }
    }
    return "/data/";
  }

  var DATA_BASE = dataBaseUrl();

  /* ── shuffle helper ── */
  function shuffle(arr){
    for (var i = arr.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }

  /* ── build card HTML for each type ── */

  function buildHowWouldYouPlay(entry, idx, total){
    var front = '<div class="ex-face ex-front">' +
      '<div class="ex-tag-row">' +
        '<span class="ex-num">#' + (idx+1) + ' of ' + total + '</span>' +
        '<span class="ex-type-pill">Find the Move</span>' +
      '</div>' +
      '<div class="ex-position">' +
        '<span class="ex-side-label">White</span>' +
        '<span class="ex-pieces">' + esc(entry.white) + '</span>' +
      '</div>' +
      '<div class="ex-position">' +
        '<span class="ex-side-label">Black</span>' +
        '<span class="ex-pieces">' + esc(entry.black) + '</span>' +
      '</div>' +
      '<div class="ex-prompt">' +
        '<span class="ex-to-move">' + esc(entry.toMove) + ' to move</span><br>' +
        'How would you play?' +
      '</div>' +
      '<div class="ex-controls">' +
        '<button class="ex-primary ex-flip-btn">Show Solution</button>' +
      '</div>' +
    '</div>';

    var solText = entry.solution.join("  ");
    var back = '<div class="ex-face ex-back">' +
      '<div class="ex-tag-row">' +
        '<span class="ex-num">#' + (idx+1) + ' of ' + total + '</span>' +
        '<span class="ex-type-pill">Solution</span>' +
      '</div>' +
      '<div class="ex-solution-label">Answer</div>' +
      '<div class="ex-solution">' + esc(solText) + '</div>' +
      (entry.site ? '<a class="ex-lichess-link" href="' + esc(entry.site) + '" target="_blank" rel="noopener">View on Lichess</a>' : '') +
      '<div class="ex-controls">' +
        '<button class="ex-flip-btn">Back to Exercise</button>' +
        '<button class="ex-primary ex-next-btn">Next &rarr;</button>' +
      '</div>' +
    '</div>';

    return front + back;
  }

  function buildDeterminePositions(entry, idx, total){
    var front = '<div class="ex-face ex-front">' +
      '<div class="ex-tag-row">' +
        '<span class="ex-num">#' + (idx+1) + ' of ' + total + '</span>' +
        '<span class="ex-type-pill">Determine Positions</span>' +
      '</div>' +
      '<div class="ex-position">' +
        '<span class="ex-side-label">White</span>' +
        '<span class="ex-pieces">' + esc(entry.white) + '</span>' +
      '</div>' +
      '<div class="ex-position">' +
        '<span class="ex-side-label">Black</span>' +
        '<span class="ex-pieces">' + esc(entry.black) + '</span>' +
      '</div>' +
      '<div class="ex-continuation">' +
        '<div class="ex-cont-label">Continuation</div>' +
        '<div class="ex-moves">' + esc(entry.continuation) + '</div>' +
      '</div>' +
      '<div class="ex-prompt">' +
        'Determine the positions of all white and black pawns and pieces.' +
      '</div>' +
      '<div class="ex-controls">' +
        '<button class="ex-primary ex-flip-btn">Show Solution</button>' +
      '</div>' +
    '</div>';

    var back = '<div class="ex-face ex-back">' +
      '<div class="ex-tag-row">' +
        '<span class="ex-num">#' + (idx+1) + ' of ' + total + '</span>' +
        '<span class="ex-type-pill">Solution</span>' +
      '</div>' +
      '<div class="ex-solution-label">Final Position</div>' +
      '<div class="ex-solution-position">' +
        '<span class="ex-side-label">White</span>' +
        '<span class="ex-pieces">' + esc(entry.solutionWhite) + '</span>' +
      '</div>' +
      '<div class="ex-solution-position">' +
        '<span class="ex-side-label">Black</span>' +
        '<span class="ex-pieces">' + esc(entry.solutionBlack) + '</span>' +
      '</div>' +
      (entry.site ? '<a class="ex-lichess-link" href="' + esc(entry.site) + '" target="_blank" rel="noopener">View on Lichess</a>' : '') +
      '<div class="ex-controls">' +
        '<button class="ex-flip-btn">Back to Exercise</button>' +
        '<button class="ex-primary ex-next-btn">Next &rarr;</button>' +
      '</div>' +
    '</div>';

    return front + back;
  }

  function buildPlayOutTheGame(entry, idx, total){
    var front = '<div class="ex-face ex-front">' +
      '<div class="ex-tag-row">' +
        '<span class="ex-num">#' + (idx+1) + ' of ' + total + '</span>' +
        '<span class="ex-type-pill">Blindfold Game</span>' +
      '</div>' +
      '<div class="ex-prompt" style="border-top:none; padding-top:0;">' +
        'Play out the game without looking at the board:' +
      '</div>' +
      '<div class="ex-continuation">' +
        '<div class="ex-moves">' + esc(entry.moves) + '</div>' +
      '</div>' +
      '<div class="ex-prompt">' +
        '<span class="ex-to-move">' + esc(entry.toMove) + ' to move</span><br>' +
        'How would you play?' +
      '</div>' +
      '<div class="ex-controls">' +
        '<button class="ex-primary ex-flip-btn">Show Solution</button>' +
      '</div>' +
    '</div>';

    var solText = entry.solution.join("  ");
    var back = '<div class="ex-face ex-back">' +
      '<div class="ex-tag-row">' +
        '<span class="ex-num">#' + (idx+1) + ' of ' + total + '</span>' +
        '<span class="ex-type-pill">Solution</span>' +
      '</div>' +
      '<div class="ex-solution-label">Answer</div>' +
      '<div class="ex-solution">' + esc(solText) + '</div>' +
      (entry.fullLine ? '<div class="ex-continuation"><div class="ex-cont-label">Full Line</div><div class="ex-moves">' + esc(entry.fullLine) + '</div></div>' : '') +
      (entry.site ? '<a class="ex-lichess-link" href="' + esc(entry.site) + '" target="_blank" rel="noopener">View on Lichess</a>' : '') +
      '<div class="ex-controls">' +
        '<button class="ex-flip-btn">Back to Exercise</button>' +
        '<button class="ex-primary ex-next-btn">Next &rarr;</button>' +
      '</div>' +
    '</div>';

    return front + back;
  }

  /* ── escape HTML ── */
  function esc(s){
    if (!s) return "";
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  /* ── deck controller ── */
  function initDeck(container){
    var cat  = container.getAttribute("data-category");
    var type = container.getAttribute("data-type");
    if (!cat || !type) return;

    var builders = {
      "how-would-you-play": buildHowWouldYouPlay,
      "determine-positions": buildDeterminePositions,
      "play-out-the-game":  buildPlayOutTheGame
    };
    var build = builders[type];
    if (!build) return;

    var url = DATA_BASE + cat + ".json";
    fetch(url).then(function(r){ return r.json(); }).then(function(data){
      if (!data || !data.length){
        container.innerHTML = '<div class="ex-empty">No exercises loaded yet.</div>';
        return;
      }
      shuffle(data);
      var idx = 0;

      function show(i){
        idx = i;
        var scene = document.createElement("div");
        scene.className = "ex-scene";
        var card = document.createElement("div");
        card.className = "ex-card";
        card.innerHTML = build(data[i], i, data.length);
        scene.appendChild(card);
        container.innerHTML = "";
        container.appendChild(scene);

        /* counter */
        var counter = document.createElement("div");
        counter.className = "ex-counter";
        counter.textContent = (i+1) + " / " + data.length;
        container.appendChild(counter);

        /* wire flip buttons */
        var flips = card.querySelectorAll(".ex-flip-btn");
        for (var f = 0; f < flips.length; f++){
          flips[f].addEventListener("click", function(){
            card.classList.toggle("flipped");
          });
        }
        /* wire next */
        var nexts = card.querySelectorAll(".ex-next-btn");
        for (var n = 0; n < nexts.length; n++){
          nexts[n].addEventListener("click", function(){
            show((idx + 1) % data.length);
          });
        }
      }
      show(0);
    }).catch(function(){
      container.innerHTML = '<div class="ex-empty">Could not load exercises.</div>';
    });
  }

  /* ── auto-init all decks on page ── */
  function boot(){
    var decks = document.querySelectorAll(".exercise-deck");
    for (var i = 0; i < decks.length; i++) initDeck(decks[i]);
  }
  if (document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
