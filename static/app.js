```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0b0b0b">
<title>MIRROR TO YOU — Private Life Concierge</title>
<link rel="stylesheet" href="/static/style.css">
</head>

<body>
<header class="topbar">
  <a class="brand" href="/">MIRROR <span>TO YOU</span></a>
  <span class="private-mode">PRIVATE MODE</span>
</header>

<main class="container">

<section class="hero">
  <p class="eyebrow">THE PRIVATE LIFE CONCIERGE</p>
  <h1>What can I take care of for you?</h1>
  <p class="intro">
    Don't search. Tell MIRROR what you need.
    Write it or speak it. MIRROR will understand, personalize,
    decide and shape the right direction for you.
  </p>

  <div class="request-box">
    <textarea id="requestInput"
      placeholder="Tell MIRROR what you need..."
      aria-label="Tell MIRROR what you need"></textarea>

    <div class="request-actions">
      <button id="voiceButton" class="icon-button" aria-label="Speak to MIRROR">◉</button>
      <button id="clearButton" class="icon-button" aria-label="Clear">×</button>
      <button id="askMirrorButton" class="primary-button">ASK MIRROR</button>
    </div>
  </div>

  <div class="suggestions">
    <button data-request="I need a private escape.">Private escape</button>
    <button data-request="Surprise me. I want something exceptional.">Surprise me</button>
    <button data-request="I want to travel somewhere special.">Travel</button>
    <button data-request="I need help with something private.">Private life</button>
  </div>
</section>


<section id="responsePanel" class="panel" hidden>
  <div class="panel-label">MIRROR RESPONSE</div>
  <div class="response-row">
    <p id="mirrorResponse"></p>
    <button id="speakButton" class="secondary-button">◉ SPEAK</button>
  </div>
</section>


<section id="understandingPanel" class="understanding" hidden></section>


<section id="planPanel" class="panel plan-panel" hidden>
  <div class="panel-label">YOUR MIRROR DIRECTION</div>

  <h2 id="planTitle">Your MIRROR proposal</h2>
  <small id="missionId" class="mission-id"></small>

  <div class="plan-meta">
    <div><small>TYPE</small><strong id="planCategory">—</strong></div>
    <div><small>PRIVACY</small><strong id="planPrivacy">—</strong></div>
    <div><small>PRIORITY</small><strong id="planPriority">—</strong></div>
    <div><small>BUDGET</small><strong id="planBudget">—</strong></div>
    <div><small>DESTINATION</small><strong id="planDestination">—</strong></div>
  </div>

  <ul id="planDetails" class="plan-details"></ul>

  <div class="direction">
    <p class="panel-label">WHAT MIRROR IS THINKING</p>
    <ol id="planSteps"></ol>
  </div>

  <div class="plan-actions">
    <button id="thisFeelsRightButton" class="primary-button">
      THIS FEELS RIGHT
    </button>

    <button id="makeDifferentButton" class="secondary-button">
      MAKE IT DIFFERENT
    </button>

    <button id="conciergeButton" class="secondary-button">
      LET CONCIERGE HANDLE IT
    </button>

    <button id="openMapsButton" class="secondary-button">
      OPEN IN GOOGLE MAPS
    </button>

    <button id="playMoodButton" class="secondary-button">
      PLAY THE MOOD
    </button>
  </div>
</section>


<section id="conciergeStatus" class="status" hidden></section>


<section class="three-points">
  <article>
    <span>01</span>
    <h3>MY MIRROR</h3>
    <p>Your preferences stay on this device so MIRROR can become increasingly aligned with you.</p>
  </article>

  <article>
    <span>02</span>
    <h3>YOUR MOMENT</h3>
    <p>Every day is different. MIRROR considers what matters to you now, not only what it learned before.</p>
  </article>

  <article>
    <span>03</span>
    <h3>PRIVATE CONCIERGE</h3>
    <p>When something requires real-world coordination, MIRROR prepares it for concierge handling.</p>
  </article>
</section>


<section class="memory-panel">
  <div>
    <p class="panel-label">MEMORY</p>
    <h2>Your MIRROR memory lives on this device.</h2>
    <p>
      MIRROR uses your preferences to personalize your experience.
      If you change devices, you can rebuild your experience privately.
    </p>
  </div>

  <div class="memory-actions">
    <button id="rebuildMemoryButton" class="secondary-button">REBUILD MY MIRROR</button>
    <button id="backupMemoryButton" class="secondary-button">BACK UP MEMORY</button>
    <button id="restoreMemoryButton" class="secondary-button">RESTORE MEMORY</button>
    <input id="memoryFile" type="file" accept=".json,application/json" hidden>
  </div>
</section>


<section class="missions">
  <div class="panel-label">CURRENT MISSIONS</div>
  <div id="missionsList"></div>
</section>

</main>


<div id="recoveryModal" class="modal" hidden>
  <div class="modal-backdrop"></div>

  <div class="modal-card">
    <button id="closeRecoveryButton" class="modal-close">×</button>

    <p class="panel-label">REBUILD YOUR MIRROR</p>
    <h2>Let's find your rhythm again.</h2>
    <p>
      A few choices are enough for MIRROR to rebuild your preferences.
    </p>

    <div id="recoveryQuestions"></div>

    <button id="saveRecoveryButton" class="primary-button">
      RESTORE MY EXPERIENCE
    </button>
  </div>
</div>


<footer>
  <strong>MIRROR TO YOU</strong>
  <span>Private by design.</span>
</footer>

<script src="/static/app.js" defer></script>
</body>
</html>
```
