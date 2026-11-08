const state = {
  events: [],
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
};
const body = document.querySelector("#events-body"),
  notice = document.querySelector("#notice");
const filters = ["search", "conflicts"].map((id) =>
  document.querySelector("#" + id),
);
const showOptions = document.querySelector("#show-options");
const showFilterLabel = document.querySelector("#show-filter-label");
const periodMode = document.querySelector("#period-mode");
const periodValue = document.querySelector("#period-value");
function updatePeriod() {
  const value = periodValue.value;
  document.querySelector("#period-label").textContent = !value
    ? "Vsi datumi"
    : periodMode.value === "date" ? formatDate(value)
    : new Intl.DateTimeFormat("sl-SI", { month: "long", year: "numeric" })
        .format(new Date(Number(value.slice(0, 4)), Number(value.slice(5, 7)) - 1, 1));
  if (value) {
    state.year = Number(value.slice(0, 4));
    state.month = Number(value.slice(5, 7));
  }
  render();
}
periodMode.addEventListener("change", () => {
  const previous = periodValue.value;
  periodValue.type = periodMode.value;
  periodValue.value = previous
    ? periodMode.value === "month" ? previous.slice(0, 7)
      : previous.length === 7 ? previous + "-01" : previous
    : "";
  document.querySelector("#period-input-label").textContent =
    periodMode.value === "date" ? "Točen datum" : "Mesec";
  updatePeriod();
});
periodValue.addEventListener("input", updatePeriod);
document.querySelector("#period-clear").addEventListener("click", () => {
  periodValue.value = "";
  updatePeriod();
  document.querySelector("#period-filter").open = false;
});
document.addEventListener("click", (event) => {
  document.querySelectorAll(".show-filter[open]").forEach((menu) => {
    if (!menu.contains(event.target)) menu.open = false;
  });
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    document.querySelectorAll(".show-filter[open]").forEach((menu) => {
      menu.open = false;
      menu.querySelector("summary").focus();
    });
  }
});
function formatDate(date) {
  const [year, month, day] = date.split("-");
  return `${day}.${month}.${year}`;
}
function getMainTitle(title) {
  if (title.startsWith("ŽBF 2")) {
    return "ŽBF 2";
  }
  return title;
}
function escapeHtml(s) {
  return String(s ?? "").replace(
    /[&<>'"]/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        c
      ],
  );
}
function selectedShows() {
  return [...showOptions.querySelectorAll("input:checked")].map((input) => input.value);
}
function updateShowFilterLabel() {
  const shows = selectedShows();
  showFilterLabel.textContent = !shows.length
    ? "Vse predstave"
    : shows.length === 1
      ? shows[0]
      : `${shows.length} predstavi`;
}
function filtered() {
  const search = filters[0].value.toLowerCase(),
    date = periodMode.value === "date" ? periodValue.value : "",
    month = periodMode.value === "month" ? periodValue.value : "",
    shows = selectedShows(),
    conflicts = filters[1].checked;

  return state.events.filter(
    (e) =>
      (!search ||
        `${e.naziv_predstave} ${e.lokacija || ""}`
          .toLowerCase()
          .includes(search)) &&
      (!date || e.datum === date) &&
      (!month || e.datum.startsWith(month)) &&
      (!shows.length || shows.includes(getMainTitle(e.naziv_predstave))) &&
      (!conflicts || e.status === "KONFLIKT"),
  );
}
function render() {
  const events = filtered();
  body.innerHTML =
    events
      .map(
        (e) =>
          `<tr><td>${formatDate(e.datum)}</td><td>${e.ura || "—"}</td><td>${escapeHtml(e.naziv_predstave)}</td><td>${escapeHtml(e.lokacija || "—")}</td><td><span class="status ${e.status === "KONFLIKT" ? "conflict" : "ok"}">${e.status}</span>${e.konflikt_s.length ? `<span class="conflict-detail">${escapeHtml(e.konflikt_s.join(", "))}</span>` : ""}</td><td class="resolved-cell"><input class="resolved-checkbox" type="checkbox" data-event-id="${e.id}" aria-label="Označi ${escapeHtml(e.naziv_predstave)} kot rešeno" ${e.reseno ? "checked" : ""} ${e.status === "KONFLIKT" ? "" : "disabled"}></td></tr>`,
      )
      .join("") ||
    '<tr><td colspan="6">Ni zadetkov za izbrane filtre.</td></tr>';
  const conflictDays = new Set(
    events.filter((e) => e.status === "KONFLIKT").map((e) => e.datum),
  ).size;
  notice.textContent = filters[1].checked
    ? `Prikazanih je ${conflictDays} konfliktnih dni (${events.length} terminov) od ${state.events.length} terminov.`
    : `Prikazanih ${events.length} od ${state.events.length} terminov. Konfliktni dnevi: ${conflictDays}.`;
  renderCalendar();
}
function renderCalendar() {
  const target = `${state.year}-${String(state.month).padStart(2, "0")}`;
  const map = {};
  state.events
    .filter((e) => e.datum.startsWith(target))
    .forEach((e) => {
      const day = Number(e.datum.slice(-2));
      map[day] ??= [];
      map[day].push(e);
    });
  document.querySelector("#calendar-title").textContent =
    new Intl.DateTimeFormat("sl-SI", { month: "long", year: "numeric" }).format(
      new Date(state.year, state.month - 1),
    );
  const start = (new Date(state.year, state.month - 1, 1).getDay() + 6) % 7,
    days = new Date(state.year, state.month, 0).getDate();
  document.querySelector("#calendar").innerHTML =
    Array.from({ length: start }, () => "<span></span>").join("") +
    Array.from({ length: days }, (_, i) => {
      const ev = map[i + 1] || [],
        conflict = ev.some((e) => e.status === "KONFLIKT");
      const names = [...new Set(ev.map((e) => e.naziv_predstave))];
      const tooltip = ev.length
        ? `${conflict ? "Konflikt" : "Termin"}: ${names.join(", ")}`
        : "";
      return `<span class="day ${ev.length ? "has-events" : ""} ${conflict ? "has-conflict" : ""}" ${tooltip ? `tabindex="0" role="img" aria-label="${escapeHtml(tooltip)}" data-tooltip="${escapeHtml(tooltip)}" title="${escapeHtml(tooltip)}"` : ""}>${i + 1}</span>`;
    }).join("");
}
async function load() {
  const res = await fetch("/api/events");
  state.events = await res.json();
  const titles = [
    ...new Set(state.events.map((e) => getMainTitle(e.naziv_predstave))),
  ].sort();
  showOptions.innerHTML = titles
    .map(
      (title) =>
        `<label><input type="checkbox" value="${escapeHtml(title)}"> ${escapeHtml(title)}</label>`,
    )
    .join("");
  updateShowFilterLabel();
  render();
}
filters.forEach((f) => f.addEventListener("input", render));
showOptions.addEventListener("change", () => {
  updateShowFilterLabel();
  render();
});
body.addEventListener("change", async (event) => {
  const checkbox = event.target;
  if (!checkbox.matches(".resolved-checkbox")) return;

  const previousValue = !checkbox.checked;
  checkbox.disabled = true;
  try {
    const response = await fetch(`/api/events/${checkbox.dataset.eventId}/resolved`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolved: checkbox.checked }),
    });
    if (!response.ok) throw new Error("Shranjevanje ni uspelo.");
    const updated = await response.json();
    state.events = state.events.map((e) => (e.id === updated.id ? updated : e));
    render();
  } catch (error) {
    checkbox.checked = previousValue;
    checkbox.disabled = false;
    notice.textContent = "Oznake ni bilo mogoče shraniti. Poskusite znova.";
  }
});
document.querySelector("#previous").onclick = () => {
  state.month--;
  if (!state.month) {
    state.month = 12;
    state.year--;
  }
  renderCalendar();
};
document.querySelector("#next").onclick = () => {
  state.month++;
  if (state.month === 13) {
    state.month = 1;
    state.year++;
  }
  renderCalendar();
};
document.querySelector("#refresh").onclick = async () => {
  notice.textContent = "Osvežujem javne vire …";
  const res = await fetch("/api/refresh", { method: "POST" }),
    data = await res.json();
  await load();
  notice.textContent = data.errors.length
    ? `Osveženo z opozorili: ${data.errors.length}.`
    : `Osveženo: ${data.added} novih, ${data.updated} posodobljenih, ${data.deleted} odstranjenih.`;
};
const exportDialog = document.querySelector("#export-dialog");
const exportPeriod = document.querySelector("#export-period");
const exportMonth = document.querySelector("#export-month");
const exportShows = document.querySelector("#export-shows");
const exportAllShows = document.querySelector("#export-all-shows");
let exportFormat = "pdf";
function exportSelection() {
  return {
    month: exportPeriod.value === "month" ? exportMonth.value : "",
    shows: exportAllShows.checked ? [] : [...exportShows.querySelectorAll("input:checked")].map(c => c.value),
  };
}
function updateExport() {
  const monthly = exportPeriod.value === "month";
  exportMonth.hidden = !monthly;
  document.querySelector("#export-month-label").hidden = !monthly;
  exportMonth.required = monthly;
  exportShows.querySelectorAll("input").forEach(c => { c.disabled = exportAllShows.checked; });
  const {month, shows} = exportSelection();
  const count = state.events.filter(e => (!monthly || (month && e.datum.startsWith(month))) &&
    (exportAllShows.checked || shows.includes(getMainTitle(e.naziv_predstave)))).length;
  document.querySelector("#export-count").textContent = "Terminov za izvoz: " + count;
  exportDialog.querySelector('[type="submit"]').disabled =
    (monthly && !month) || (!exportAllShows.checked && !shows.length);
}
document.querySelectorAll('a[href="/export.xlsx"], a[href="/export.pdf"]').forEach(link => {
  link.addEventListener("click", event => {
    event.preventDefault();
    exportFormat = link.getAttribute("href").endsWith("xlsx") ? "xlsx" : "pdf";
    document.querySelector("#export-title").textContent = "Izvoz terminov — " + (exportFormat === "xlsx" ? "Excel" : "PDF");
    exportPeriod.value = "all";
    exportMonth.value = "";
    exportAllShows.checked = true;
    exportShows.innerHTML = [...new Set(state.events.map(e => getMainTitle(e.naziv_predstave)))].sort()
      .map(title => '<label><input type="checkbox" value="' + escapeHtml(title) + '"> ' + escapeHtml(title) + '</label>').join("");
    updateExport();
    exportDialog.showModal();
  });
});
document.querySelector("#export-form").addEventListener("input", updateExport);
document.querySelector("#export-cancel").onclick = () => exportDialog.close();
document.querySelector("#export-form").addEventListener("submit", event => {
  event.preventDefault();
  const {month, shows} = exportSelection();
  const params = new URLSearchParams();
  if (month) params.set("month", month);
  shows.forEach(show => params.append("shows", show));
  const link = document.createElement("a");
  link.href = "/export." + exportFormat + "?" + params.toString();
  link.download = "termini-predstav." + exportFormat;
  document.body.append(link);
  link.click();
  link.remove();
  exportDialog.close();
});
load();
