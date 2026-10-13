function todayIsoLocal() {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

function isPastOrToday(dateStr) {
  return dateStr <= todayIsoLocal();
}

function isStrengthType(value) {
  const t = String(value || "").toLowerCase();
  return t.includes("сил") || t.includes("strength");
}

function isStrengthExercise(ex) {
  return isStrengthType(ex.exercise_type);
}

function isStrengthWorkout(w) {
  if (isStrengthType(w.workout_type)) return true;
  const exs = w.exercises || [];
  if (!exs.length) return false;
  return exs.every(isStrengthExercise);
}

function exerciseHasPlannedVolume(ex) {
  const km = ex.planned_km;
  if (km != null && Number(km) > 0) return true;
  const mins = ex.planned_minutes;
  if (mins != null && Number(mins) > 0) return true;
  return false;
}

function workoutRequestsDistance(w) {
  if (w.requests_distance === false) return false;
  if (w.requests_distance === true) return true;
  if (isStrengthWorkout(w)) return false;
  return (w.exercises || []).some(exerciseHasPlannedVolume);
}

function formatKm(value) {
  if (value == null || value === "") return "—";
  return String(value);
}

function formatExerciseLogLine(ex, log) {
  if (!log) return "нет отчёта";
  if (isStrengthExercise(ex)) {
    if (log.done_as_planned) return "как в плане ✓";
    if (log.sets_done != null || log.reps_done != null) {
      return `${log.sets_done ?? "?"}×${log.reps_done ?? "?"}`;
    }
    return log.done ? "выполнено" : "не отмечено";
  }
  return log.done ? "выполнено ✓" : "не выполнено";
}
