"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AudioPlayer from "@/components/AudioPlayer";
import HistoryList from "@/components/HistoryList";
import {
  fetchVoices,
  synthesizeSpeech,
  type SynthesizeSuccessResponse,
  type Voice,
} from "@/lib/api-client";
import {
  formatVoiceOptionLabel,
  getVoiceDescriptionZh,
  getVoiceProfile,
} from "@/lib/voice-profiles";
import styles from "./page.module.css";

const TAG_PRESETS = [
  { label: "慢速", tag: "[slowly] " },
  { label: "強調", tag: "[emphasis] " },
  { label: "停頓", tag: "[pause] " },
  { label: "興奮", tag: "[excited] " },
  { label: "很慢", tag: "[very slow] " },
  { label: "耳語", tag: "[whisper] " },
];

const STYLE_OPTIONS = [
  { label: "自然清晰", value: "Natural and clear" },
  { label: "新聞主播", value: "News anchor, crisp and professional" },
  { label: "正式演講", value: "Formal keynote, authoritative and measured" },
  { label: "說故事", value: "Storyteller, warm and expressive" },
  { label: "輕鬆對話", value: "Casual conversational, friendly and relaxed" },
  { label: "戲劇朗誦", value: "Dramatic recitation, theatrical emphasis" },
];

const PACING_OPTIONS = [
  { label: "很慢", value: "Very slow, deliberate and measured" },
  { label: "偏慢", value: "Moderately slow, unhurried" },
  { label: "中速", value: "Moderate and natural" },
  { label: "偏快", value: "Moderately fast, energetic" },
  { label: "很快", value: "Very fast, rapid delivery" },
];

const ACCENT_OPTIONS = [
  { label: "美式英文", value: "American English" },
  { label: "英式英文", value: "British English" },
  { label: "澳式英文", value: "Australian English" },
  { label: "依文稿語言", value: "Accent matching the transcript language" },
];

const PREF_STORAGE_KEY = "txt2speech_prefs";

interface StoredPrefs {
  voice?: string;
  style?: string;
  pacing?: string;
  accent?: string;
}

function loadPrefs(): StoredPrefs {
  try {
    const raw = localStorage.getItem(PREF_STORAGE_KEY);
    if (raw) return JSON.parse(raw) as StoredPrefs;
  } catch {
    /* ignore */
  }
  return {};
}

function savePrefs(prefs: StoredPrefs) {
  try {
    localStorage.setItem(PREF_STORAGE_KEY, JSON.stringify(prefs));
  } catch {
    /* ignore */
  }
}

export default function Home() {
  const [text, setText] = useState("");
  const [voice, setVoice] = useState("");
  const [style, setStyle] = useState(() => loadPrefs().style ?? "");
  const [pacing, setPacing] = useState(() => loadPrefs().pacing ?? "");
  const [accent, setAccent] = useState(() => loadPrefs().accent ?? "");
  const [source, setSource] = useState<"text" | "md">("text");

  const [voices, setVoices] = useState<Voice[]>([]);
  const [voicesLoading, setVoicesLoading] = useState(true);
  const [voicesError, setVoicesError] = useState<string | null>(null);

  const [synthesizing, setSynthesizing] = useState(false);
  const [synthesizeError, setSynthesizeError] = useState<string | null>(null);
  const [result, setResult] = useState<SynthesizeSuccessResponse | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    savePrefs({ voice, style, pacing, accent });
  }, [voice, style, pacing, accent]);

  useEffect(() => {
    let cancelled = false;

    fetchVoices()
      .then((data) => {
        if (!cancelled) {
          setVoices(data.voices);
          setVoice((currentVoice) => {
            if (currentVoice) return currentVoice;
            const savedVoice = loadPrefs().voice;
            if (savedVoice && data.voices.some((v) => v.name === savedVoice)) return savedVoice;
            return data.voices[0]?.name || "";
          });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setVoicesError(
            err instanceof Error ? err.message : "無法載入音色清單",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setVoicesLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const insertTagAtCursor = useCallback(
    (tag: string) => {
      const ta = textareaRef.current;
      if (!ta) return;

      const start = ta.selectionStart;
      const end = ta.selectionEnd;
      const before = text.slice(0, start);
      const after = text.slice(end);

      const newText = before + tag + after;
      setText(newText);

      requestAnimationFrame(() => {
        ta.focus();
        const pos = start + tag.length;
        ta.setSelectionRange(pos, pos);
      });
    },
    [text],
  );

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = () => {
        const content = typeof reader.result === "string" ? reader.result : "";
        setText(content);
        setSource("md");
        setSynthesizeError(null);
      };
      reader.onerror = () => {
        setSynthesizeError("無法讀取檔案");
      };
      reader.readAsText(file);
    },
    [],
  );

  const handleGenerate = useCallback(async () => {
    if (!text.trim()) {
      setSynthesizeError("請先輸入講稿內容。");
      return;
    }
    if (!voice) {
      setSynthesizeError("請先選擇音色。");
      return;
    }

    setSynthesizeError(null);
    setResult(null);
    setSynthesizing(true);

    try {
      const response = await synthesizeSpeech({
        text: text.trim(),
        voice,
        style: style.trim() || undefined,
        pacing: pacing.trim() || undefined,
        accent: accent.trim() || undefined,
        source,
      });
      setResult(response);
      setHistoryRefreshKey((k) => k + 1);
    } catch (err: unknown) {
      setSynthesizeError(
        err instanceof Error ? err.message : "語音合成失敗",
      );
    } finally {
      setSynthesizing(false);
    }
  }, [text, voice, style, pacing, accent, source]);

  const resetSource = useCallback(() => {
    setSource("text");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const selectedVoice = voices.find((v) => v.name === voice);
  const selectedVoiceProfile = selectedVoice
    ? getVoiceProfile(selectedVoice.name)
    : undefined;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>txt2speech</h1>
        <p className={styles.subtitle}>演講練習 TTS 工具</p>
      </header>

      <main className={styles.main}>
        <section className={styles.section}>
          <label htmlFor="voice-select" className={styles.label}>
            音色
          </label>
          {voicesLoading && (
            <p className={styles.hint}>載入音色中...</p>
          )}
          {voicesError && (
            <p className={styles.errorText}>{voicesError}</p>
          )}
          {!voicesLoading && !voicesError && voices.length === 0 && (
            <p className={styles.hint}>目前沒有可用音色。</p>
          )}
          {!voicesLoading && voices.length > 0 && (
            <>
              <select
                id="voice-select"
                className={styles.select}
                value={voice}
                onChange={(e) => setVoice(e.target.value)}
              >
                {voices.map((v) => (
                  <option key={v.name} value={v.name}>
                    {formatVoiceOptionLabel(v)}
                  </option>
                ))}
              </select>

              {selectedVoice && selectedVoiceProfile && (
                <div className={styles.voiceDetail}>
                  <div className={styles.voiceTags}>
                    <span className={styles.voiceTag}>{selectedVoiceProfile.gender}</span>
                    <span className={styles.voiceTag}>{selectedVoiceProfile.pitch}</span>
                    <span className={styles.voiceTag}>{selectedVoiceProfile.tone}</span>
                    <span className={styles.voiceTag}>
                      官方特徵：{getVoiceDescriptionZh(selectedVoice)}
                    </span>
                  </div>
                  <p className={styles.voiceHint}>{selectedVoiceProfile.character}</p>
                </div>
              )}
            </>
          )}
        </section>

        <section className={styles.section}>
          <div className={styles.rowBetween}>
            <label htmlFor="text-input" className={styles.label}>
              講稿內容
            </label>
            <div className={styles.sourceRow}>
              {source === "md" && (
                <span className={styles.sourceBadge}>
                  .md &nbsp;
                  <button
                    type="button"
                    className={styles.clearSourceBtn}
                    onClick={resetSource}
                    aria-label="清除 .md 來源"
                  >
                    x
                  </button>
                </span>
              )}
              <label className={styles.fileUploadLabel}>
                上傳 .md
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".md,.markdown,text/markdown"
                  className={styles.fileInput}
                  onChange={handleFileUpload}
                />
              </label>
            </div>
          </div>

          <div className={styles.tagRow}>
            {TAG_PRESETS.map((p) => (
              <button
                key={p.tag}
                type="button"
                className={styles.tagBtn}
                onClick={() => insertTagAtCursor(p.tag)}
              >
                {p.label}
              </button>
            ))}
          </div>

          <textarea
            ref={textareaRef}
            id="text-input"
            className={styles.textarea}
            rows={10}
            placeholder="貼上或輸入你的演講稿..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </section>

        <section className={styles.section}>
          <p className={styles.label}>朗讀提示</p>
          <div className={styles.notesGrid}>
            <div className={styles.noteField}>
              <label htmlFor="style-select" className={styles.sublabel}>
                風格
              </label>
              <select
                id="style-select"
                className={styles.select}
                value={style}
                onChange={(e) => setStyle(e.target.value)}
              >
                <option value="">不指定</option>
                {STYLE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className={styles.noteField}>
              <label htmlFor="pacing-select" className={styles.sublabel}>
                語速
              </label>
              <select
                id="pacing-select"
                className={styles.select}
                value={pacing}
                onChange={(e) => setPacing(e.target.value)}
              >
                <option value="">不指定</option>
                {PACING_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className={styles.noteField}>
              <label htmlFor="accent-select" className={styles.sublabel}>
                口音
              </label>
              <select
                id="accent-select"
                className={styles.select}
                value={accent}
                onChange={(e) => setAccent(e.target.value)}
              >
                <option value="">不指定</option>
                {ACCENT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <button
            type="button"
            className={styles.generateBtn}
            disabled={synthesizing || text.trim().length === 0 || !voice}
            onClick={handleGenerate}
          >
            {synthesizing ? "生成中..." : "生成語音"}
          </button>

          {synthesizing && (
            <p className={styles.hint}>
              正在合成語音，可能需要一點時間。
            </p>
          )}
          {synthesizeError && (
            <p className={styles.errorText}>{synthesizeError}</p>
          )}
        </section>

        {result && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>生成結果</h2>
            <AudioPlayer audioUrl={result.audio_url} />

            <div className={styles.metadata}>
              <p className={styles.metaLabel}>合成資訊</p>
              <ul className={styles.metaList}>
                <li>
                  <strong>ID:</strong> {result.id}
                </li>
                <li>
                  <strong>建立時間：</strong>{" "}
                  {new Date(result.created_at).toLocaleString("zh-TW")}
                </li>
                <li>
                  <strong>摘要：</strong> {result.metadata.text_excerpt}
                </li>
                <li>
                  <strong>字數：</strong> {result.metadata.char_count}
                </li>
                <li>
                  <strong>來源：</strong> {result.metadata.source === "md" ? ".md" : "文字"}
                </li>
                <li>
                  <strong>音色：</strong> {result.metadata.voice}
                </li>
                {result.metadata.pacing && (
                  <li>
                    <strong>語速：</strong> {result.metadata.pacing}
                  </li>
                )}
                {result.metadata.style && (
                  <li>
                    <strong>風格：</strong> {result.metadata.style}
                  </li>
                )}
                {result.metadata.accent && (
                  <li>
                    <strong>口音：</strong> {result.metadata.accent}
                  </li>
                )}
              </ul>
            </div>
          </section>
        )}

        <HistoryList refreshKey={historyRefreshKey} />
      </main>
    </div>
  );
}
