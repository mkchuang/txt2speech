import type { Voice } from "@/lib/api-client";

export interface VoiceProfile {
  gender: "男聲" | "女聲";
  tone: string;
  pitch: string;
  character: string;
}

const VOICE_PROFILES: Record<string, VoiceProfile> = {
  Zephyr: {
    gender: "女聲",
    tone: "明亮活潑",
    pitch: "中高音",
    character: "適合開場、親切簡報、正向內容",
  },
  Puck: {
    gender: "男聲",
    tone: "開朗有精神",
    pitch: "中音",
    character: "適合產品介紹、教學、輕鬆演講",
  },
  Charon: {
    gender: "男聲",
    tone: "資訊清楚",
    pitch: "中低音",
    character: "適合解說、簡報旁白、知識型內容",
  },
  Kore: {
    gender: "女聲",
    tone: "堅定俐落",
    pitch: "中高音",
    character: "適合重點宣告、短句強調",
  },
  Fenrir: {
    gender: "男聲",
    tone: "興奮有戲劇感",
    pitch: "中音",
    character: "適合活動宣傳、角色語氣、強情緒段落",
  },
  Leda: {
    gender: "女聲",
    tone: "年輕清晰",
    pitch: "中音",
    character: "適合教學、活潑簡報、輕快內容",
  },
  Orus: {
    gender: "男聲",
    tone: "堅定低沉",
    pitch: "低音",
    character: "適合正式簡報、權威敘事、重點收束",
  },
  Aoede: {
    gender: "女聲",
    tone: "輕快通透",
    pitch: "中高音",
    character: "適合故事敘述、溫和開場",
  },
  Callirrhoe: {
    gender: "女聲",
    tone: "輕鬆自然",
    pitch: "中音",
    character: "適合日常說明、友善簡報",
  },
  Autonoe: {
    gender: "女聲",
    tone: "明亮清楚",
    pitch: "中高音",
    character: "適合正向訊息、短講、開場白",
  },
  Enceladus: {
    gender: "男聲",
    tone: "氣聲感",
    pitch: "中低音",
    character: "適合柔和旁白、沉浸式內容",
  },
  Iapetus: {
    gender: "男聲",
    tone: "清楚直接",
    pitch: "中音",
    character: "適合教學步驟、技術說明",
  },
  Umbriel: {
    gender: "男聲",
    tone: "沉穩好親近",
    pitch: "中低音",
    character: "適合長段旁白、企業簡報",
  },
  Algieba: {
    gender: "男聲",
    tone: "平滑穩定",
    pitch: "中低音",
    character: "適合專業解說、節奏穩的稿件",
  },
  Despina: {
    gender: "女聲",
    tone: "柔順溫暖",
    pitch: "中音",
    character: "適合歡迎詞、品牌敘事、溫和內容",
  },
  Erinome: {
    gender: "女聲",
    tone: "清晰沉著",
    pitch: "中音",
    character: "適合教育內容、正式說明",
  },
  Algenib: {
    gender: "男聲",
    tone: "粗礫低沉",
    pitch: "低音",
    character: "適合強烈敘事、成熟角色、警示語氣",
  },
  Rasalgethi: {
    gender: "男聲",
    tone: "知識型",
    pitch: "中音",
    character: "適合 podcast、訪談、思考型段落",
  },
  Laomedeia: {
    gender: "女聲",
    tone: "活潑親切",
    pitch: "中音",
    character: "適合 e-learning、輕快解說",
  },
  Achernar: {
    gender: "女聲",
    tone: "柔和",
    pitch: "中高音",
    character: "適合安撫語氣、慢速旁白",
  },
  Alnilam: {
    gender: "男聲",
    tone: "堅定穩重",
    pitch: "中低音",
    character: "適合正式報告、關鍵結論",
  },
  Schedar: {
    gender: "男聲",
    tone: "均衡平穩",
    pitch: "中音",
    character: "適合一般演講、長稿練習",
  },
  Gacrux: {
    gender: "女聲",
    tone: "成熟穩重",
    pitch: "中低音",
    character: "適合嚴肅主題、沉著敘事",
  },
  Pulcherrima: {
    gender: "女聲",
    tone: "前進感強",
    pitch: "中高音",
    character: "適合推進節奏、倡議型內容",
  },
  Achird: {
    gender: "男聲",
    tone: "友善自然",
    pitch: "中音",
    character: "適合親民簡報、產品 demo",
  },
  Zubenelgenubi: {
    gender: "男聲",
    tone: "隨性低沉",
    pitch: "低音",
    character: "適合放鬆口吻、成熟旁白",
  },
  Vindemiatrix: {
    gender: "女聲",
    tone: "溫柔沉靜",
    pitch: "中低音",
    character: "適合反思型段落、慢節奏內容",
  },
  Sadachbia: {
    gender: "男聲",
    tone: "生動有活力",
    pitch: "中低音",
    character: "適合強節奏段落、宣傳稿",
  },
  Sadaltager: {
    gender: "男聲",
    tone: "專業知性",
    pitch: "中音",
    character: "適合課程、研討會、知識分享",
  },
  Sulafat: {
    gender: "女聲",
    tone: "溫暖有說服力",
    pitch: "中音",
    character: "適合品牌敘事、溫和號召",
  },
};

const DESCRIPTION_ZH: Record<string, string> = {
  Bright: "明亮",
  Upbeat: "活潑",
  Informative: "資訊型",
  Firm: "堅定",
  Excitable: "興奮",
  Youthful: "年輕",
  Breezy: "輕快",
  "Easy-going": "輕鬆",
  Breathy: "氣聲",
  Clear: "清晰",
  Smooth: "平滑",
  Gravelly: "粗礫",
  Soft: "柔和",
  Even: "均衡",
  Mature: "成熟",
  Forward: "前進感",
  Friendly: "友善",
  Casual: "隨性",
  Gentle: "溫柔",
  Lively: "生動",
  Knowledgeable: "知性",
  Warm: "溫暖",
};

export function getVoiceProfile(name: string): VoiceProfile | undefined {
  return VOICE_PROFILES[name];
}

export function getVoiceDescriptionZh(voice: Voice): string {
  return DESCRIPTION_ZH[voice.description] ?? voice.description;
}

export function formatVoiceOptionLabel(voice: Voice): string {
  const profile = getVoiceProfile(voice.name);
  const description = getVoiceDescriptionZh(voice);

  if (!profile) {
    return `${voice.name} - ${description}`;
  }

  return [
    voice.name,
    profile.gender,
    description,
    profile.pitch,
    profile.tone,
  ].join(" ｜ ");
}

export function formatVoiceSummary(name: string): string {
  const profile = getVoiceProfile(name);
  if (!profile) return name;

  return `${name}｜${profile.gender}・${profile.pitch}・${profile.tone}`;
}
