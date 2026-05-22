export const t = {
  appName: 'Transcritor',
  tagline: 'Transcrição de áudio e vídeo com Whisper',

  nav: {
    dashboard: 'Início',
    upload: 'Novo upload',
    settings: 'Configurações'
  },

  status: {
    queued: 'Na fila',
    processing: 'Transcrevendo',
    done: 'Concluído',
    failed: 'Falhou',
    cancelled: 'Cancelado'
  } as const,

  dashboard: {
    title: 'Suas transcrições',
    empty: 'Nenhuma transcrição ainda. Comece enviando um arquivo.',
    newJob: 'Novo upload',
    refresh: 'Atualizar'
  },

  upload: {
    title: 'Enviar arquivo',
    helper: 'Arraste um arquivo de áudio ou vídeo ou clique para selecionar. Suporta arquivos de vários GB com retomada automática.',
    dropHere: 'Solte o arquivo aqui',
    selectButton: 'Selecionar arquivo',
    languageLabel: 'Idioma do áudio',
    languageAuto: 'Detectar automaticamente',
    start: 'Iniciar transcrição',
    cancel: 'Cancelar envio',
    pause: 'Pausar',
    resume: 'Retomar',
    progress: 'Enviado',
    failed: 'Falha no envio. Tente novamente.',
    success: 'Upload concluído. Iniciando transcrição…'
  },

  job: {
    detail: 'Detalhes da transcrição',
    progress: 'Progresso',
    duration: 'Duração',
    language: 'Idioma',
    model: 'Modelo',
    sizeOnDisk: 'Tamanho',
    createdAt: 'Criado em',
    error: 'Erro',
    segments: 'Segmentos',
    noSegments: 'Aguardando transcrição…',
    actions: 'Ações',
    cancel: 'Cancelar',
    delete: 'Excluir',
    export: 'Exportar',
    confirmDelete: 'Excluir esta transcrição? Esta ação não pode ser desfeita.'
  },

  export: {
    srt: 'Legenda SRT',
    vtt: 'Legenda VTT',
    txt: 'Texto puro',
    json: 'JSON estruturado',
    docx: 'Documento Word'
  },

  errors: {
    generic: 'Algo deu errado. Tente novamente.'
  }
};

export const languages = [
  { code: '', label: 'Detectar automaticamente' },
  { code: 'pt', label: 'Português' },
  { code: 'en', label: 'Inglês' },
  { code: 'es', label: 'Espanhol' },
  { code: 'fr', label: 'Francês' },
  { code: 'de', label: 'Alemão' },
  { code: 'it', label: 'Italiano' },
  { code: 'ja', label: 'Japonês' },
  { code: 'zh', label: 'Chinês' }
];
