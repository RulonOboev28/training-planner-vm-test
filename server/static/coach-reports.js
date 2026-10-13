let coachSelectedAthleteId = null;

async function refreshCoachGroups() {
  const groupsEl = document.getElementById("coach-groups-list");
  const ungroupedEl = document.getElementById("coach-ungrouped-list");
  const metaEl = document.getElementById("coach-roster-meta");
  if (!groupsEl) return;

  try {
    const data = await apiAuth("/coach/roster/groups");
    groupsEl.innerHTML = "";
    ungroupedEl.innerHTML = "";

    const onRoster = (data.groups || []).reduce(
      (n, g) => n + (g.members || []).filter((m) => m.on_roster).length,
      0,
    ) + (data.ungrouped || []).length;

    metaEl.textContent = data.publication_version
      ? `В группе на сервере: ${onRoster}. План v${data.publication_version}.`
      : `В группе: ${(data.ungrouped || []).length}. Опубликуйте план, чтобы увидеть подгруппы из конструктора.`;

    if (!(data.groups || []).length) {
      groupsEl.innerHTML = "<li class=\"hint\">Подгруппы появятся после публикации плана с группами.</li>";
    } else {
      for (const g of data.groups) {
        const li = document.createElement("li");
        li.className = "coach-group-item";
        const title = document.createElement("strong");
        title.textContent = g.title;
        li.appendChild(title);
        const ul = document.createElement("ul");
        ul.className = "coach-member-list";
        const rosterMembers = (g.members || []).filter((m) => m.on_roster && m.server_athlete_id);
        if (!rosterMembers.length) {
          ul.innerHTML = "<li class=\"hint\">Никого из группы ещё не приняли приглашение</li>";
        } else {
          for (const m of rosterMembers) {
            ul.appendChild(coachMemberButton(m));
          }
        }
        li.appendChild(ul);
        groupsEl.appendChild(li);
      }
    }

    if (!(data.ungrouped || []).length) {
      ungroupedEl.innerHTML = "<li class=\"hint\">Все спортсmenы в подгруппах плана</li>";
    } else {
      for (const m of data.ungrouped) {
        ungroupedEl.appendChild(coachMemberButton(m));
      }
    }
  } catch (e) {
    groupsEl.innerHTML = `<li class="error">${humanError(e.message || e)}</li>`;
  }
}

function coachMemberButton(m) {
  const li = document.createElement("li");
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "link coach-athlete-link";
  btn.textContent = `${m.display_name || m.login} (@${m.login})`;
  btn.addEventListener("click", () => openCoachAthleteReport(m.server_athlete_id, m.display_name || m.login));
  li.appendChild(btn);
  return li;
}

async function openCoachAthleteReport(athleteId, name) {
  coachSelectedAthleteId = athleteId;
  const panel = document.getElementById("coach-athlete-panel");
  const title = document.getElementById("coach-athlete-title");
  const body = document.getElementById("coach-athlete-body");
  title.textContent = `Отчёт: ${name}`;
  body.innerHTML = "<p class=\"hint\">Загрузка…</p>";
  panel.hidden = false;
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
  await loadCoachAthleteWeekReport(athleteId);
}

async function loadCoachAthleteWeekReport(athleteId) {
  const body = document.getElementById("coach-athlete-body");
  try {
    const report = await apiAuth(`/coach/athletes/${athleteId}/reports/week`);
    body.innerHTML = "";
    body.appendChild(renderCoachWeekSummary(report.summary, report.from, report.to));
    body.appendChild(renderCoachWorkoutsReadonly(report.workouts));
  } catch (e) {
    body.innerHTML = `<p class="error">${humanError(e.message || e)}</p>`;
  }
}

function renderCoachWeekSummary(summary, from, to) {
  const box = document.createElement("div");
  box.className = "coach-week-summary";
  box.innerHTML = `
    <h3 class="section-title">Неделя ${formatDateRu(from)} — ${formatDateRu(to)}</h3>
    <dl class="summary-dl">
      <dt>Отчётов за прошедшие дни</dt><dd>${summary.reported_workouts} / ${summary.past_workouts}</dd>
      <dt>Км всего (сумма)</dt><dd>${formatKm(summary.total_distance_km)}</dd>
      <dt>Км скоростной (сумма)</dt><dd>${formatKm(summary.speed_distance_km)}</dd>
      <dt>Средний пульс (по тренировкам с отчётом)</dt><dd>${summary.hr_avg_mean != null ? summary.hr_avg_mean : "—"}</dd>
    </dl>
  `;
  return box;
}

function renderCoachWorkoutsReadonly(workouts) {
  const wrap = document.createElement("div");
  wrap.className = "coach-workouts-readonly";
  let lastDate = null;
  for (const w of workouts || []) {
    if (w.date !== lastDate) {
      lastDate = w.date;
      const dayEl = document.createElement("h2");
      dayEl.className = "plan-day";
      dayEl.textContent = formatDateRu(w.date);
      wrap.appendChild(dayEl);
    }

    const card = document.createElement("article");
    card.className = "workout-card";

    const h = document.createElement("h3");
    h.textContent = w.workout_title || "Тренировка";
    card.appendChild(h);

    const list = document.createElement("ul");
    list.className = "exercise-list";
    for (const ex of w.exercises || []) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "exercise-btn exercise-btn-inline";
      btn.textContent = ex.title || "Упражнение";
      btn.addEventListener("click", () => openExerciseDialog(ex));
      li.appendChild(btn);
      list.appendChild(li);
    }
    card.appendChild(list);

    const report = document.createElement("div");
    report.className = "workout-report coach-readonly-report";
    const sess = w.session;
    const showDist = workoutRequestsDistance(w);
    const distLines = showDist
      ? `<p>Км всего: <strong>${formatKm(sess && sess.total_distance_km)}</strong> · Скоростной: <strong>${formatKm(sess && sess.speed_distance_km)}</strong></p>`
      : "";
    const hrLine = `<p>Пульс ср.: <strong>${sess && sess.hr_avg != null ? sess.hr_avg : "—"}</strong> · макс.: <strong>${sess && sess.hr_max != null ? sess.hr_max : "—"}</strong></p>`;
    report.innerHTML = `<p class="report-heading">Отчёт</p>${distLines}${hrLine}`;

    const exUl = document.createElement("ul");
    exUl.className = "coach-ex-log-list";
    for (const row of w.exercise_logs || []) {
      const ex = (w.exercises || []).find((e) => e.id === row.exercise_id) || { title: row.title };
      const li = document.createElement("li");
      li.textContent = `${ex.title}: ${formatExerciseLogLine(ex, row.log)}`;
      exUl.appendChild(li);
    }
    report.appendChild(exUl);
    card.appendChild(report);
    wrap.appendChild(card);
  }
  return wrap;
}

document.getElementById("coach-athlete-close")?.addEventListener("click", () => {
  document.getElementById("coach-athlete-panel").hidden = true;
});
