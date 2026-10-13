function sessionKey(workoutId, dateStr) {
  return `${dateStr}|${workoutId}`;
}

function exerciseKey(exerciseId, dateStr) {
  return `${dateStr}|${exerciseId}`;
}

function numVal(input) {
  if (!input || input.value === "") return null;
  const n = Number(input.value.replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

function intVal(input) {
  const n = numVal(input);
  return n === null ? null : Math.round(n);
}

function buildSessionFieldsHtml(sess, showDistance) {
  const distBlock = showDistance
    ? `
          <label>Км всего<input type="number" step="0.1" min="0" data-field="total_km" value="${sess.total_distance_km ?? ""}" placeholder="не бегал"></label>
          <label>Км скоростной<input type="number" step="0.1" min="0" data-field="speed_km" value="${sess.speed_distance_km ?? ""}"></label>
        `
    : "";
  return `
        <p class="report-heading">Отчёт за тренировку</p>
        <div class="report-grid">
          ${distBlock}
          <label>Пульс ср.<input type="number" min="30" max="250" data-field="hr_avg" value="${sess.hr_avg ?? ""}"></label>
          <label>Пульс макс.<input type="number" min="30" max="250" data-field="hr_max" value="${sess.hr_max ?? ""}"></label>
        </div>
      `;
}

async function renderAthletePlanWithReports(week) {
  const canvas = document.getElementById("plan-canvas");
  canvas.innerHTML = "";
  const workouts = week.workouts || [];
  if (!workouts.length) {
    canvas.innerHTML = "<p class=\"hint\">На эту неделю тренировок нет.</p>";
    return;
  }

  let exerciseLogs = [];
  let sessionLogs = [];
  try {
    const q = `?from=${encodeURIComponent(week.from)}&to=${encodeURIComponent(week.to)}`;
    exerciseLogs = await apiAuth(`/athlete/log${q}`);
    sessionLogs = await apiAuth(`/athlete/log/session${q}`);
  } catch {
    /* показываем план без сохранённых отчётов */
  }

  const exMap = new Map();
  for (const row of exerciseLogs) {
    exMap.set(exerciseKey(row.exercise_id, row.log_date), row);
  }
  const sessMap = new Map();
  for (const row of sessionLogs) {
    sessMap.set(sessionKey(row.workout_id, row.log_date), row);
  }

  let lastDate = null;
  for (const w of workouts) {
    if (w.date !== lastDate) {
      lastDate = w.date;
      const dayEl = document.createElement("h2");
      dayEl.className = "plan-day";
      const past = isPastOrToday(w.date);
      dayEl.textContent = `${formatDateRu(w.date)}${past ? "" : " · впереди"}`;
      canvas.appendChild(dayEl);
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
      li.className = "exercise-row";
      const title = document.createElement("button");
      title.type = "button";
      title.className = "exercise-btn exercise-btn-inline";
      title.textContent = ex.title || "Упражнение";
      title.addEventListener("click", () => openExerciseDialog(ex));
      li.appendChild(title);
      list.appendChild(li);
    }
    card.appendChild(list);

    if (isPastOrToday(w.date)) {
      const report = document.createElement("div");
      report.className = "workout-report";

      const sess = sessMap.get(sessionKey(w.workout_id, w.date)) || {};
      const showDistance = workoutRequestsDistance(w);

      report.innerHTML = buildSessionFieldsHtml(sess, showDistance);
      if (!showDistance) {
        const note = document.createElement("p");
        note.className = "hint report-no-km";
        note.textContent = "Километраж не нужен для этой тренировки (силовая или без бега/длительности в плане).";
        report.insertBefore(note, report.querySelector(".report-grid"));
      }

      const exBlock = document.createElement("div");
      exBlock.className = "exercise-reports";
      for (const ex of w.exercises || []) {
        const saved = exMap.get(exerciseKey(ex.id, w.date)) || {};
        const strength = isStrengthExercise(ex);
        const plannedSets = ex.sets != null ? ex.sets : "";
        const plannedReps = ex.reps != null ? ex.reps : "";
        const asPlanned = saved.done_as_planned !== false;

        const row = document.createElement("div");
        row.className = "ex-report-row";
        row.dataset.exerciseId = ex.id;

        if (strength) {
          row.innerHTML = `
            <p class="ex-report-title">${ex.title} <span class="tag">силовое</span></p>
            <label class="check-line">
              <input type="checkbox" data-field="as_planned" ${asPlanned ? "checked" : ""}>
              Сделал(а) как в плане${plannedSets ? ` (${plannedSets}×${plannedReps})` : ""}
            </label>
            <div class="custom-reps ${asPlanned ? "hidden" : ""}">
              <label>Подходы<input type="number" min="0" data-field="sets" value="${saved.sets_done ?? ""}"></label>
              <label>Повторы<input type="number" min="0" data-field="reps" value="${saved.reps_done ?? ""}"></label>
            </div>
          `;
          const cb = row.querySelector('[data-field="as_planned"]');
          const custom = row.querySelector(".custom-reps");
          cb.addEventListener("change", () => {
            custom.classList.toggle("hidden", cb.checked);
          });
        } else {
          row.innerHTML = `
            <p class="ex-report-title">${ex.title}</p>
            <label class="check-line">
              <input type="checkbox" data-field="done" ${saved.done ? "checked" : ""}>
              Выполнено
            </label>
          `;
        }
        exBlock.appendChild(row);
      }
      report.appendChild(exBlock);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "primary report-save";
      saveBtn.textContent = "Сохранить отчёт";
      saveBtn.addEventListener("click", async () => {
        saveBtn.disabled = true;
        try {
          const sessionBody = {
            workout_id: w.workout_id,
            log_date: w.date,
            hr_avg: intVal(report.querySelector('[data-field="hr_avg"]')),
            hr_max: intVal(report.querySelector('[data-field="hr_max"]')),
          };
          if (showDistance) {
            sessionBody.total_distance_km = numVal(report.querySelector('[data-field="total_km"]'));
            sessionBody.speed_distance_km = numVal(report.querySelector('[data-field="speed_km"]'));
          } else {
            sessionBody.total_distance_km = null;
            sessionBody.speed_distance_km = null;
          }
          await apiAuth("/athlete/log/session", {
            method: "POST",
            body: JSON.stringify(sessionBody),
          });
          for (const row of exBlock.querySelectorAll(".ex-report-row")) {
            const exId = row.dataset.exerciseId;
            const strengthEl = row.querySelector('[data-field="as_planned"]');
            let body;
            if (strengthEl) {
              const asPlanned = strengthEl.checked;
              body = {
                exercise_id: exId,
                workout_id: w.workout_id,
                log_date: w.date,
                done: true,
                done_as_planned: asPlanned,
                sets_done: asPlanned ? null : intVal(row.querySelector('[data-field="sets"]')),
                reps_done: asPlanned ? null : intVal(row.querySelector('[data-field="reps"]')),
              };
            } else {
              body = {
                exercise_id: exId,
                workout_id: w.workout_id,
                log_date: w.date,
                done: row.querySelector('[data-field="done"]').checked,
                done_as_planned: true,
              };
            }
            await apiAuth("/athlete/log", { method: "POST", body: JSON.stringify(body) });
          }
          saveBtn.textContent = "Сохранено";
          setTimeout(() => {
            saveBtn.textContent = "Сохранить отчёт";
            saveBtn.disabled = false;
          }, 1500);
        } catch (e) {
          saveBtn.disabled = false;
          alert(humanError(e.message || e));
        }
      });
      report.appendChild(saveBtn);
      card.appendChild(report);
    } else {
      const hint = document.createElement("p");
      hint.className = "hint report-future";
      hint.textContent = "Отчёт можно будет заполнить после этой даты.";
      card.appendChild(hint);
    }

    canvas.appendChild(card);
  }
}
