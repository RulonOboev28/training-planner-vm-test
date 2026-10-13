const TOKEN_KEYS = { coach: "coach_token", athlete: "athlete_token" };



let role = null;



const screens = {

  role: document.getElementById("screen-role"),

  auth: document.getElementById("screen-auth"),

  coachHome: document.getElementById("screen-coach-home"),

  athletePlan: document.getElementById("screen-athlete-plan"),

};



const panelLogin = document.getElementById("panel-login");

const panelRegister = document.getElementById("panel-register");



function show(name) {

  Object.values(screens).forEach((el) => {

    if (el) el.hidden = true;

  });

  if (screens[name]) screens[name].hidden = false;

}



function tokenFor(r) {

  return localStorage.getItem(TOKEN_KEYS[r]);

}



function setToken(r, value) {

  if (value) localStorage.setItem(TOKEN_KEYS[r], value);

  else localStorage.removeItem(TOKEN_KEYS[r]);

}



function humanError(message) {

  const m = String(message || "").trim();

  const map = {

    "Invalid credentials": "Неверный логин или пароль.",

    "Email already registered": "Эта почта уже зарегистрирована — перейдите на «Вход».",

    "Username already taken": "Этот логин уже занят — придумайте другой псевдоним.",

    "Not Found": "Сервер устарел: остановите uvicorn и запустите снова из папки server.",

    "Field required": "Заполните почту и пароль. Если ошибка повторяется — перезапустите сервер (Ctrl+F5).",

    "Invite cooldown: once per 24 hours":

      "Повторное приглашение — не чаще одного раза в сутки. Проверьте логин.",

  };

  if (map[m]) return map[m];

  if (m.includes("at least 8")) return "Пароль должен быть не короче 8 символов.";

  if (m.includes("Field required")) return map["Field required"];

  return m || "Ошибка";

}



function authLoginBody(login, password) {

  return { login: login.trim(), password };

}



async function api(path, options = {}) {

  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };

  const res = await fetch(path, { ...options, headers });

  const text = await res.text();

  let data = null;

  try {

    data = text ? JSON.parse(text) : null;

  } catch {

    data = { detail: text };

  }

  if (!res.ok) {

    const detail = data?.detail;

    const msg = Array.isArray(detail)

      ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")

      : detail || res.statusText;

    throw new Error(msg || "Ошибка");

  }

  return data;

}



async function apiAuth(path, options = {}) {

  const token = tokenFor(role);

  return api(path, {

    ...options,

    headers: {

      ...(options.headers || {}),

      Authorization: `Bearer ${token}`,

    },

  });

}



function roleTitle(r) {

  return r === "coach" ? "Тренер" : "Спортсmen";

}



function setAuthMode(mode) {

  const isLogin = mode === "login";

  document.querySelectorAll(".mode-btn").forEach((btn) => {

    btn.classList.toggle("mode-active", btn.dataset.mode === mode);

  });

  panelLogin.hidden = !isLogin;

  panelRegister.hidden = isLogin;

  document.getElementById("login-error").hidden = true;

  document.getElementById("register-error").hidden = true;

}



function openAuth(selectedRole) {

  role = selectedRole;

  if (tokenFor(role)) {

    openHome();

    return;

  }

  document.getElementById("auth-role-title").textContent = roleTitle(role);

  setAuthMode("login");

  show("auth");

}



async function openHome() {

  if (!role || !tokenFor(role)) {

    show("role");

    return;

  }

  if (role === "coach") {

    show("coachHome");

    await refreshCoachHome();

    return;

  }

  show("athletePlan");

  await refreshAthleteHome();

}



function formatDateRu(iso) {

  const [y, m, d] = iso.split("-");

  return `${d}.${m}.${y}`;

}



function exerciseDetailRows(ex) {

  const rows = [];

  if (ex.exercise_type) rows.push(["Тип", ex.exercise_type]);

  if (ex.planned_minutes != null) rows.push(["Минуты", String(ex.planned_minutes)]);

  if (ex.planned_km != null) rows.push(["Км", String(ex.planned_km)]);

  if (ex.intensity_percent != null) rows.push(["Интенсивность", `${ex.intensity_percent}%`]);

  if (ex.hr_zone) rows.push(["Пульсовая зона", ex.hr_zone]);

  if (ex.weight_kg != null) rows.push(["Вес", `${ex.weight_kg} кг`]);

  if (ex.sets != null) rows.push(["Подходы", String(ex.sets)]);

  if (ex.reps != null) rows.push(["Повторы", String(ex.reps)]);

  return rows;

}



function openExerciseDialog(ex) {

  const dlg = document.getElementById("exercise-dialog");

  document.getElementById("exercise-dialog-title").textContent = ex.title || "Упражнение";

  const body = document.getElementById("exercise-dialog-body");

  body.innerHTML = "";

  for (const [label, value] of exerciseDetailRows(ex)) {

    const dt = document.createElement("dt");

    dt.textContent = label;

    const dd = document.createElement("dd");

    dd.textContent = value;

    body.appendChild(dt);

    body.appendChild(dd);

  }

  if (!body.children.length) {

    const dt = document.createElement("dt");

    dt.textContent = "Описание";

    const dd = document.createElement("dd");

    dd.textContent = "Нет дополнительных полей.";

    body.appendChild(dt);

    body.appendChild(dd);

  }

  dlg.showModal();

}



function renderPlanCanvas(plan) {

  const canvas = document.getElementById("plan-canvas");

  canvas.innerHTML = "";

  const workouts = plan.workouts || [];

  if (!workouts.length) {

    canvas.innerHTML = "<p class=\"hint\">На эту неделю тренировок нет.</p>";

    return;

  }

  let lastDate = null;

  for (const w of workouts) {

    if (w.date !== lastDate) {

      lastDate = w.date;

      const dayEl = document.createElement("h2");

      dayEl.className = "plan-day";

      dayEl.textContent = formatDateRu(w.date);

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

      const btn = document.createElement("button");

      btn.type = "button";

      btn.className = "exercise-btn";

      btn.textContent = ex.title || "Упражнение";

      btn.addEventListener("click", () => openExerciseDialog(ex));

      li.appendChild(btn);

      list.appendChild(li);

    }

    card.appendChild(list);

    canvas.appendChild(card);

  }

}



async function renderInvites(invites) {

  const box = document.getElementById("athlete-invites");

  box.innerHTML = "";

  if (!invites.length) {

    box.hidden = true;

    return;

  }

  box.hidden = false;

  const title = document.createElement("p");

  title.className = "invite-title";

  title.textContent = "Приглашения от тренеров";

  box.appendChild(title);

  const warn = document.createElement("p");

  warn.className = "invite-warn";

  warn.textContent =

    "Проверьте, что это ваш тренер. Отказ без причины может задержать повторное приглашение на сутки.";

  box.appendChild(warn);



  for (const inv of invites) {

    const row = document.createElement("div");

    row.className = "invite-row";

    const label = document.createElement("span");

    label.textContent = inv.coach_display_name || "Тренер";

    row.appendChild(label);

    const accept = document.createElement("button");

    accept.type = "button";

    accept.className = "primary invite-accept";

    accept.textContent = "Принять";

    accept.addEventListener("click", async () => {

      await apiAuth(`/athlete/invites/${inv.id}/accept`, { method: "POST" });

      await refreshAthleteHome();

    });

    const reject = document.createElement("button");

    reject.type = "button";

    reject.className = "link invite-reject";

    reject.textContent = "Отклонить";

    reject.addEventListener("click", async () => {

      await apiAuth(`/athlete/invites/${inv.id}/reject`, { method: "POST" });

      await refreshAthleteHome();

    });

    row.appendChild(accept);

    row.appendChild(reject);

    box.appendChild(row);

  }

}



function inviteStatusRu(status) {

  const map = {

    pending: "ожидает",

    accepted: "в группе",

    rejected: "отклонено",

  };

  return map[status] || status;

}



async function refreshCoachHome() {

  const errEl = document.getElementById("coach-invite-error");

  if (errEl) errEl.hidden = true;

  try {

    const [invites, roster] = await Promise.all([

      apiAuth("/coach/invites"),

      apiAuth("/coach/roster/sync"),

    ]);

    const invList = document.getElementById("coach-invites-list");

    invList.innerHTML = "";

    if (!invites.length) {

      invList.innerHTML = "<li class=\"hint\">Пока нет приглашений</li>";

    } else {

      for (const inv of invites) {

        const li = document.createElement("li");

        li.textContent = `${inv.target_login} — ${inviteStatusRu(inv.status)}`;

        invList.appendChild(li);

      }

    }

    await refreshCoachGroups();

  } catch (e) {

    if (errEl) {

      errEl.textContent = humanError(e.message || e);

      errEl.hidden = false;

    }

  }

}



async function refreshAthleteHome() {

  const statusEl = document.getElementById("athlete-plan-status");

  statusEl.textContent = "Загрузка…";

  try {

    const me = await apiAuth("/athlete/me");

    let invites = [];

    try {

      invites = await apiAuth("/athlete/invites");

    } catch {

      /* инвайты не должны блокировать просмотр плана */

    }

    const week = await apiAuth("/athlete/plan/week");

    await renderInvites(invites);

    if (!me.in_group) {

      statusEl.textContent = "Примите приглашение от тренера, чтобы увидеть план.";

      document.getElementById("plan-canvas").innerHTML = "";

      return;

    }

    statusEl.textContent = `Вы в группе. План с ${week.from} по ${week.to}. Заполните отчёты за прошедшие дни.`;

    await renderAthletePlanWithReports(week);

  } catch (e) {

    statusEl.textContent = humanError(e.message || e);

  }

}



document.querySelectorAll(".choice-btn").forEach((btn) => {

  btn.addEventListener("click", () => openAuth(btn.dataset.role));

});



document.querySelectorAll(".mode-btn").forEach((btn) => {

  btn.addEventListener("click", () => setAuthMode(btn.dataset.mode));

});



document.getElementById("back-from-auth").addEventListener("click", () => {

  role = null;

  show("role");

});



document.getElementById("btn-do-login").addEventListener("click", async () => {

  const errEl = document.getElementById("login-error");

  errEl.hidden = true;

  const login = document.getElementById("login-login").value;

  const password = document.getElementById("login-password").value;

  try {

    const prefix = role === "coach" ? "/auth/coach" : "/auth/athlete";

    const data = await api(`${prefix}/login`, {

      method: "POST",

      body: JSON.stringify(authLoginBody(login, password)),

    });

    setToken(role, data.access_token);

    openHome();

  } catch (e) {

    errEl.textContent = humanError(e.message || e);

    errEl.hidden = false;

  }

});



document.getElementById("btn-do-register").addEventListener("click", async () => {

  const errEl = document.getElementById("register-error");

  errEl.hidden = true;

  const body = {

    email: document.getElementById("reg-email").value.trim(),

    login: document.getElementById("reg-login").value.trim(),

    password: document.getElementById("reg-password").value,

  };

  try {

    const prefix = role === "coach" ? "/auth/coach" : "/auth/athlete";

    await api(`${prefix}/register`, {

      method: "POST",

      body: JSON.stringify(body),

    });

    const login = await api(`${prefix}/login`, {

      method: "POST",

      body: JSON.stringify(authLoginBody(body.login, body.password)),

    });

    setToken(role, login.access_token);

    openHome();

  } catch (e) {

    errEl.textContent = humanError(e.message || e);

    errEl.hidden = false;

  }

});



document.querySelectorAll(".btn-logout").forEach((btn) => {

  btn.addEventListener("click", () => {

    if (role) setToken(role, null);

    role = null;

    show("role");

  });

});



document.getElementById("btn-coach-invite").addEventListener("click", async () => {

  const errEl = document.getElementById("coach-invite-error");

  errEl.hidden = true;

  const login = document.getElementById("coach-invite-login").value.trim();

  if (!login) {

    errEl.textContent = "Введите логин спортсmena.";

    errEl.hidden = false;

    return;

  }

  try {

    await apiAuth("/coach/invites", {

      method: "POST",

      body: JSON.stringify({ login }),

    });

    document.getElementById("coach-invite-login").value = "";

    await refreshCoachHome();

  } catch (e) {

    errEl.textContent = humanError(e.message || e);

    errEl.hidden = false;

  }

});



document.getElementById("btn-coach-publish").addEventListener("click", async () => {

  const errEl = document.getElementById("coach-publish-error");

  const okEl = document.getElementById("coach-publish-result");

  errEl.hidden = true;

  okEl.hidden = true;

  const fileInput = document.getElementById("coach-publish-file");

  const file = fileInput.files && fileInput.files[0];

  if (!file) {

    errEl.textContent = "Выберите файл publish_pack.json.";

    errEl.hidden = false;

    return;

  }

  try {

    const text = await file.text();

    const body = JSON.parse(text);

    const resp = await apiAuth("/coach/plan/publish", {

      method: "POST",

      body: JSON.stringify(body),

    });

    let msg = `Опубликовано, версия ${resp.version}. Спортсmenов в пакете: ${resp.athletes_in_payload}.`;

    const creds = resp.new_athlete_credentials || [];

    if (creds.length) {

      msg += ` Созданы логины: ${creds.map((c) => c.login).join(", ")}.`;

    }

    okEl.textContent = msg;

    okEl.hidden = false;

    await refreshCoachHome();

  } catch (e) {

    errEl.textContent = humanError(e.message || e);

    errEl.hidden = false;

  }

});



show("role");

