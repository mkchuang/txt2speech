"use client";

import { useCallback, useEffect, useState } from "react";
import {
  audioDownloadUrl,
  deleteHistoryItem,
  fetchHistory,
  type HistoryItem,
} from "@/lib/api-client";
import styles from "@/app/page.module.css";

const PAGE_LIMIT = 50;

interface HistoryListProps {
  refreshKey: number;
}

export default function HistoryList({ refreshKey }: HistoryListProps) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [lastLoadedKey, setLastLoadedKey] = useState(-1);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loading = lastLoadedKey !== refreshKey;

  useEffect(() => {
    let cancelled = false;

    fetchHistory(PAGE_LIMIT, 0)
      .then((data) => {
        if (!cancelled) {
          setItems(data.items);
          setTotal(data.total);
          setHasMore(data.has_more);
          setError(null);
          setLastLoadedKey(refreshKey);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load history");
          setLastLoadedKey(refreshKey);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const handleLoadMore = useCallback(async () => {
    if (loadingMore) return;

    setLoadingMore(true);
    setError(null);

    try {
      const data = await fetchHistory(PAGE_LIMIT, items.length);
      setItems((prev) => [...prev, ...data.items]);
      setTotal(data.total);
      setHasMore(data.has_more);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load more items");
    } finally {
      setLoadingMore(false);
    }
  }, [items.length, loadingMore]);

  const handleDelete = useCallback(async (id: string) => {
    if (!window.confirm("Delete this history item?")) return;

    setDeletingId(id);
    try {
      await deleteHistoryItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setTotal((prev) => prev - 1);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to delete item");
    } finally {
      setDeletingId(null);
    }
  }, []);

  if (loading) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>History</h2>
        <p className={styles.hint}>Loading history...</p>
      </section>
    );
  }

  if (error && items.length === 0) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>History</h2>
        <p className={styles.errorText}>{error}</p>
      </section>
    );
  }

  if (items.length === 0) {
    return (
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>History</h2>
        <p className={styles.hint}>No history yet. Generate some speech to see it here.</p>
      </section>
    );
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>
        History{total > 0 ? ` (${items.length} of ${total})` : ""}
      </h2>

      {error && <p className={styles.errorText}>{error}</p>}

      <div className={styles.historyList}>
        {items.map((item) => {
          const isCompleted = item.status === "completed";

          return (
            <div key={item.id} className={styles.historyItem}>
              <div className={styles.historyItemHead}>
                <div className={styles.historyItemTitle}>
                  <span className={styles.historyItemVoice}>{item.voice}</span>
                  {!isCompleted && (
                    <span className={styles.historyStatus}>{item.status}</span>
                  )}
                </div>
                <span className={styles.historyItemDate}>
                  {new Date(item.created_at).toLocaleString()}
                </span>
              </div>

              <p className={styles.historyItemExcerpt}>{item.text_excerpt}</p>

              {isCompleted ? (
                <audio
                  controls
                  src={item.audio_url}
                  preload="none"
                  className={styles.historyAudio}
                />
              ) : (
                <p className={styles.historyUnavailable}>Audio unavailable</p>
              )}

              <div className={styles.historyItemActions}>
                {isCompleted && (
                  <a
                    href={audioDownloadUrl(item.audio_url)}
                    download
                    className={styles.historyActionBtn}
                  >
                    Download
                  </a>
                )}
                <button
                  type="button"
                  className={styles.historyDeleteBtn}
                  disabled={deletingId === item.id}
                  onClick={() => handleDelete(item.id)}
                >
                  {deletingId === item.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {hasMore && (
        <button
          type="button"
          className={styles.loadMoreBtn}
          disabled={loadingMore}
          onClick={handleLoadMore}
        >
          {loadingMore ? "Loading..." : "Load more"}
        </button>
      )}
    </section>
  );
}
