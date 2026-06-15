"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AudioPlayer from "@/components/AudioPlayer";
import {
  fetchVoices,
  synthesizeSpeech,
  type SynthesizeSuccessResponse,
  type Voice,
} from "@/lib/api-client";
import styles from "./page.module.css";

const TAG_PRESETS = [
  { label: "Slowly", tag: "[slowly] " },
  { label: "Emphasize", tag: "[emphasis] " },
  { label: "Pause", tag: "[pause] " },
  { label: "Excited", tag: "[excited] " },
  { label: "Very Slow", tag: "[very slow] " },
  { label: "Whisper", tag: "[whisper] " },
];

export default function Home() {
  const [text, setText] = useState("");
  const [voice, setVoice] = useState("");
  const [style, setStyle] = useState("");
  const [pacing, setPacing] = useState("");
  const [accent, setAccent] = useState("");
  const [source, setSource] = useState<"text" | "md">("text");

  const [voices, setVoices] = useState<Voice[]>([]);
  const [voicesLoading, setVoicesLoading] = useState(true);
  const [voicesError, setVoicesError] = useState<string | null>(null);

  const [synthesizing, setSynthesizing] = useState(false);
  const [synthesizeError, setSynthesizeError] = useState<string | null>(null);
  const [result, setResult] = useState<SynthesizeSuccessResponse | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;

    fetchVoices()
      .then((data) => {
        if (!cancelled) {
          setVoices(data.voices);
          setVoice((currentVoice) => currentVoice || data.voices[0]?.name || "");
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setVoicesError(
            err instanceof Error ? err.message : "Failed to load voices",
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
        setSynthesizeError("Failed to read file");
      };
      reader.readAsText(file);
    },
    [],
  );

  const handleGenerate = useCallback(async () => {
    if (!text.trim()) {
      setSynthesizeError("Please enter some text.");
      return;
    }
    if (!voice) {
      setSynthesizeError("Please select a voice.");
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
    } catch (err: unknown) {
      setSynthesizeError(
        err instanceof Error ? err.message : "Synthesis failed",
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

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>txt2speech</h1>
        <p className={styles.subtitle}>Speech Practice Tool</p>
      </header>

      <main className={styles.main}>
        <section className={styles.section}>
          <label htmlFor="voice-select" className={styles.label}>
            Voice
          </label>
          {voicesLoading && (
            <p className={styles.hint}>Loading voices...</p>
          )}
          {voicesError && (
            <p className={styles.errorText}>{voicesError}</p>
          )}
          {!voicesLoading && !voicesError && voices.length === 0 && (
            <p className={styles.hint}>No voices available.</p>
          )}
          {!voicesLoading && voices.length > 0 && (
            <select
              id="voice-select"
              className={styles.select}
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
            >
              {voices.map((v) => (
                <option key={v.name} value={v.name}>
                  {v.name} - {v.description}
                </option>
              ))}
            </select>
          )}
        </section>

        <section className={styles.section}>
          <div className={styles.rowBetween}>
            <label htmlFor="text-input" className={styles.label}>
              Speech Text
            </label>
            <div className={styles.sourceRow}>
              {source === "md" && (
                <span className={styles.sourceBadge}>
                  .md &nbsp;
                  <button
                    type="button"
                    className={styles.clearSourceBtn}
                    onClick={resetSource}
                    aria-label="Clear .md source"
                  >
                    x
                  </button>
                </span>
              )}
              <label className={styles.fileUploadLabel}>
                Upload .md
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
            placeholder="Paste or type your speech text here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </section>

        <section className={styles.section}>
          <p className={styles.label}>Director&apos;s Notes</p>
          <div className={styles.notesGrid}>
            <div className={styles.noteField}>
              <label htmlFor="style-input" className={styles.sublabel}>
                Style
              </label>
              <input
                id="style-input"
                className={styles.textInput}
                type="text"
                placeholder="e.g. news anchor, storyteller"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
              />
            </div>
            <div className={styles.noteField}>
              <label htmlFor="pacing-input" className={styles.sublabel}>
                Pacing
              </label>
              <input
                id="pacing-input"
                className={styles.textInput}
                type="text"
                placeholder="e.g. slow and clear, moderate"
                value={pacing}
                onChange={(e) => setPacing(e.target.value)}
              />
            </div>
            <div className={styles.noteField}>
              <label htmlFor="accent-input" className={styles.sublabel}>
                Accent
              </label>
              <input
                id="accent-input"
                className={styles.textInput}
                type="text"
                placeholder="e.g. American, British"
                value={accent}
                onChange={(e) => setAccent(e.target.value)}
              />
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
            {synthesizing ? "Generating..." : "Generate Speech"}
          </button>

          {synthesizing && (
            <p className={styles.hint}>
              Synthesizing speech... this may take a moment.
            </p>
          )}
          {synthesizeError && (
            <p className={styles.errorText}>{synthesizeError}</p>
          )}
        </section>

        {result && (
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Result</h2>
            <AudioPlayer audioUrl={result.audio_url} />

            <div className={styles.metadata}>
              <p className={styles.metaLabel}>Metadata</p>
              <ul className={styles.metaList}>
                <li>
                  <strong>ID:</strong> {result.id}
                </li>
                <li>
                  <strong>Created:</strong>{" "}
                  {new Date(result.created_at).toLocaleString()}
                </li>
                <li>
                  <strong>Excerpt:</strong> {result.metadata.text_excerpt}
                </li>
                <li>
                  <strong>Characters:</strong> {result.metadata.char_count}
                </li>
                <li>
                  <strong>Source:</strong> {result.metadata.source}
                </li>
                <li>
                  <strong>Voice:</strong> {result.metadata.voice}
                </li>
                {result.metadata.pacing && (
                  <li>
                    <strong>Pacing:</strong> {result.metadata.pacing}
                  </li>
                )}
                {result.metadata.style && (
                  <li>
                    <strong>Style:</strong> {result.metadata.style}
                  </li>
                )}
                {result.metadata.accent && (
                  <li>
                    <strong>Accent:</strong> {result.metadata.accent}
                  </li>
                )}
              </ul>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
