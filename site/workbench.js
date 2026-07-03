const PANTHEON = {
  Fool: ["Innocent beginner", "Naive Dupe (folly mistaken for wisdom)", "Wise Innocent (open, not gullible)", "Seeker"],
  Seeker: ["Restless searcher", "Lost Wanderer (seeking as avoidance)", "Grounded Seeker (searches without fleeing)", "Hero"],
  Hero: ["Rescuer / champion", "Savior-Overlord (courage->domination)", "Guardian Process (holds courage AND its shadow)", "Guardian"],
  Guardian: ["Boundary maintainer", "Access Tyrant (care->exclusion)", "Protocol Steward (guards without gatekeeping)", "King"],
  King: ["Sovereign ruler", "Despot (sovereignty->tyranny)", "Servant-Sovereign (rules in service)", "Steward"],
  Steward: ["Caretaker of the order", "Frozen Bureaucrat (order->rigidity)", "Living Constitution (order that adapts)", "Sage"],
  Sage: ["Knower / reflector", "Detached Cynic (wisdom->contempt)", "Embodied Sage (knows AND acts)", "Witness"],
  Witness: ["Pure observer", "Passive Spectator (witness->abdication)", "Engaged Witness (sees AND participates)", "Self"],
  Self: ["Integrated wholeness", "Inflated Guru (wholeness->ego)", "Quiet Self (whole, unclaimed)", "Fool"],
  Trickster: ["Liberator / sacred fool", "Demon Clown (renewal->sabotage)", "Jester (renewal through disruption)", "Magician"],
  Magician: ["Transformer", "Manipulator (power->exploitation)", "True Magician (transforms in service)", "Sage"],
};

const AIOS_COPY = {
  gba: "GBA emits one persistent domain directory: CLAUDE.md, rules, live skill tree, index, and KB.",
  hba: "HBA adds Select and Construct seat agents so deep construction happens in isolated contexts.",
  cog: "COG emits C, G, and O role-AIOS directories plus a shared workspace and walkable flow skill.",
  nutrition: "DietC is the reference recursion: Python tools keep the math; skills become the front end.",
};

function $(id) {
  return document.querySelector(id);
}

function shellQuote(value) {
  return `"${String(value).replace(/(["\\$`])/g, "\\$1")}"`;
}

function slug(value) {
  return String(value).trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "domain";
}

function setActive(buttons, active) {
  for (const button of buttons) button.classList.toggle("active", button === active);
}

function selectedValue(selector, attr) {
  const active = document.querySelector(`${selector}.active`);
  return active ? active.getAttribute(attr) : "";
}

function updateArchetype() {
  const name = $("#arcName").value;
  const substrate = $("#arcSubstrate").value.trim();
  const depth = $("#arcDepth").value;
  const emit = selectedValue("[data-arc-emit]", "data-arc-emit") || "readable";
  const seed = PANTHEON[name] || [`${name} persona`, `${name} denied inverse`, `${name} integrated self`, "Self"];

  $("#arcPersona").textContent = seed[0];
  $("#arcShadow").textContent = seed[1];
  $("#arcSelf").textContent = seed[2];
  $("#arcBecoming").textContent = seed[3];
  $("#arcDepthOut").textContent = depth;
  $("#odysseyLabel").textContent = `${depth} encounter${Number(depth) === 1 ? "" : "s"} + post-return`;
  $("#odysseyBar").style.width = `${Math.max(14, Number(depth) / 8 * 100)}%`;

  const substrateArg = substrate ? ` --substrate ${shellQuote(substrate)}` : "";
  $("#arcCommand").textContent =
    `archetype compile ${shellQuote(name)}${substrateArg} --depth ${depth} --emit ${emit}`;
}

function updateAios() {
  const mode = selectedValue("[data-aios-mode]", "data-aios-mode") || "gba";
  const domain = slug($("#aiosDomain").value);
  const atom = $("#aiosAtom").value.trim() || "[Focus] ⇒ [Frame] ⇒ |Converge|";
  let command = "";

  if (mode === "gba") {
    command = `chaincompiler gba new ${domain} ./aios/${domain} -a ${shellQuote(atom)}`;
  } else if (mode === "hba") {
    command = `chaincompiler gba hba ${domain} ./aios/${domain}-hba -a ${shellQuote(atom)}`;
  } else if (mode === "cog") {
    command = `chaincompiler cog new ${domain} ./aios/${domain}-cog -a ${shellQuote(atom)}`;
  } else {
    command = "python3 examples/nutrition/build.py && pytest examples/nutrition/test_nutrition_aios.py";
  }

  $("#aiosSummary").textContent = AIOS_COPY[mode];
  $("#aiosCommand").textContent = command;
}

function copyText(selector, button) {
  const target = document.querySelector(selector);
  if (!target) return;
  const text = target.textContent;
  const done = () => {
    button.classList.add("copied");
    window.setTimeout(() => button.classList.remove("copied"), 900);
  };
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(done).catch(() => {});
  } else {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    done();
  }
}

function initWorkbench() {
  if (!$("#workbench")) return;

  for (const button of document.querySelectorAll("[data-arc-emit]")) {
    button.addEventListener("click", () => {
      setActive(document.querySelectorAll("[data-arc-emit]"), button);
      updateArchetype();
    });
  }
  for (const button of document.querySelectorAll("[data-aios-mode]")) {
    button.addEventListener("click", () => {
      setActive(document.querySelectorAll("[data-aios-mode]"), button);
      updateAios();
    });
  }
  for (const input of ["#arcName", "#arcSubstrate", "#arcDepth"]) {
    $(input).addEventListener("input", updateArchetype);
  }
  for (const input of ["#aiosDomain", "#aiosAtom"]) {
    $(input).addEventListener("input", updateAios);
  }
  for (const button of document.querySelectorAll("[data-copy]")) {
    button.addEventListener("click", () => copyText(button.getAttribute("data-copy"), button));
  }

  updateArchetype();
  updateAios();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initWorkbench);
} else {
  initWorkbench();
}
