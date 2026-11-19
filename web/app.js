(() => {
  "use strict";
  const payload = window.MUSICPROMPT_DATA || { summary: {}, prompts: [] };
  const prompts = payload.prompts;
  const state = { visible: 12 };
  const $ = (id) => document.getElementById(id);
  const summary = payload.summary;
  $("stat-total").textContent = summary.total_prompts ?? 0;
  $("stat-curated").textContent = summary.curated_prompts ?? 0;
  $("stat-bpm").textContent = summary.with_bpm ?? 0;
  $("stat-verified").textContent = summary.verified_prompts ?? 0;

  const genres = [...new Set(prompts.flatMap(p => p.genres))].sort();
  genres.forEach(genre => {
    const option = document.createElement("option");
    option.value = genre;
    option.textContent = genre;
    $("genre").appendChild(option);
  });

  function toast(message) {
    $("toast").textContent = message;
    $("toast").classList.add("show");
    setTimeout(() => $("toast").classList.remove("show"), 1600);
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    toast("已复制到剪贴板");
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function filteredPrompts() {
    const query = $("search").value.trim().toLocaleLowerCase();
    const genre = $("genre").value;
    const platform = $("platform").value;
    const minScore = Number($("min-score").value);
    const sort = $("sort").value;
    const filtered = prompts.filter(prompt => {
      const haystack = [prompt.title, prompt.title_zh, prompt.style_prompt,
        prompt.style_prompt_zh, ...prompt.genres, ...prompt.instruments,
        ...prompt.moods].join(" ").toLocaleLowerCase();
      return (!query || haystack.includes(query)) &&
        (!genre || prompt.genres.includes(genre)) &&
        (!platform || prompt.target_platform === platform) &&
        prompt.text_quality_score >= minScore;
    });
    return filtered.sort((a, b) => {
      if (sort === "title") return a.title.localeCompare(b.title);
      if (sort === "bpm") return (b.bpm || -1) - (a.bpm || -1);
      return b.text_quality_score - a.text_quality_score || a.title.localeCompare(b.title);
    });
  }

  function createCard(prompt) {
    const card = element("article", "prompt-card");
    const top = element("div", "card-top");
    top.appendChild(element("h3", "card-title", prompt.title));
    top.appendChild(element("span", "score", prompt.text_quality_score.toFixed(2).replace(/\.00$/, "")));
    card.appendChild(top);
    const badges = element("div", "badges");
    [prompt.target_platform, ...prompt.genres].slice(0, 6).forEach(value => badges.appendChild(element("span", "badge", value)));
    if (prompt.bpm) badges.appendChild(element("span", "badge origin", `${prompt.bpm} BPM · ${prompt.bpm_origin}`));
    if (prompt.key_signature) badges.appendChild(element("span", "badge origin", `${prompt.key_signature} · ${prompt.key_origin}`));
    card.appendChild(badges);
    card.appendChild(element("p", "prompt-text", prompt.style_prompt));
    const translation = element("div", "translation", prompt.style_prompt_zh || "暂无中文翻译");
    translation.hidden = true;
    card.appendChild(translation);
    const actions = element("div", "card-actions");
    const copy = element("button", "", "复制英文 Prompt");
    copy.type = "button";
    copy.addEventListener("click", () => copyText(prompt.style_prompt));
    const expand = element("button", "", "展开与翻译");
    expand.type = "button";
    expand.addEventListener("click", () => {
      card.classList.toggle("expanded");
      translation.hidden = !translation.hidden;
      expand.textContent = translation.hidden ? "展开与翻译" : "收起";
    });
    actions.append(copy, expand);
    card.appendChild(actions);
    return card;
  }

  function render() {
    const filtered = filteredPrompts();
    const visible = filtered.slice(0, state.visible);
    $("results").replaceChildren(...visible.map(createCard));
    $("result-count").textContent = `${filtered.length} 条结果`;
    $("active-filter").textContent = filtered.length ? `显示 ${visible.length} / ${filtered.length} 条；文本分仅用于描述 Prompt 文本。` : "";
    if (!filtered.length) $("results").appendChild(element("div", "empty", "没有匹配结果，试试减少筛选条件。"));
    $("load-more").hidden = visible.length >= filtered.length;
  }

  ["search", "genre", "platform", "min-score", "sort"].forEach(id => {
    $(id).addEventListener(id === "search" ? "input" : "change", () => { state.visible = 12; render(); });
  });
  $("load-more").addEventListener("click", () => { state.visible += 12; render(); });

  const mappings = {
    genres: [["独立流行", "indie pop"], ["流行", "pop"], ["摇滚", "rock"], ["电子", "electronic"], ["民谣", "folk"], ["嘻哈", "hip hop"], ["氛围", "ambient"]],
    moods: [["克制", "restrained"], ["治愈", "healing"], ["忧郁", "melancholic"], ["明亮", "uplifting"], ["黑暗", "dark"], ["浪漫", "romantic"]],
    vocals: [["女声", "female vocals"], ["男声", "male vocals"], ["纯音乐", "instrumental"]],
    instruments: [["钢琴", "piano"], ["合成器", "synthesizer"], ["吉他", "guitar"], ["贝斯", "bass"], ["弦乐", "strings"], ["鼓", "drums"]]
  };
  const matches = (text, pairs) => pairs.filter(([key]) => text.includes(key)).map(([, value]) => value);

  $("compose-button").addEventListener("click", () => {
    const idea = $("idea").value.trim();
    if (!idea) { toast("请先输入创作意图"); return; }
    const bpm = idea.match(/(\d{2,3})\s*BPM/i);
    const moods = matches(idea, mappings.moods);
    const parts = [$("compose-genre").value.trim() || matches(idea, mappings.genres)[0] || "pop"];
    if (moods.length) parts.push(moods.join(", "));
    if (bpm && Number(bpm[1]) >= 40 && Number(bpm[1]) <= 220) parts.push(`${bpm[1]} BPM`);
    parts.push(...matches(idea, mappings.vocals));
    if (idea.includes("中文") && !idea.includes("纯音乐")) parts.push("Chinese lyrics");
    parts.push(...matches(idea, mappings.instruments));
    parts.push(`creative direction: ${idea}`);
    $("composed-output").value = parts.join(", ");
  });
  $("copy-composed").addEventListener("click", () => {
    if ($("composed-output").value) copyText($("composed-output").value);
    else toast("请先生成 Prompt");
  });
  render();
})();
