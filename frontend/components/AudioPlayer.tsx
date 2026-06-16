"use client";

import { audioDownloadUrl } from "@/lib/api-client";

interface AudioPlayerProps {
  audioUrl: string;
}

export default function AudioPlayer({ audioUrl }: AudioPlayerProps) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "8px",
      }}
    >
      <audio
        controls
        src={audioUrl}
        style={{ width: "100%" }}
        preload="auto"
      />
      <a
        href={audioDownloadUrl(audioUrl)}
        download
        style={{
          display: "inline-block",
          padding: "6px 14px",
          border: "1px solid #ccc",
          borderRadius: "6px",
          fontSize: "0.875rem",
          textDecoration: "none",
          color: "inherit",
          width: "fit-content",
        }}
      >
        下載 WAV
      </a>
    </div>
  );
}
