/**
 * ====================================================================================================
 *                                           MAY ROGA LLC
 *                         Open Than Go / Wellness Travel Architecture
 *                                  DYNAMIC DATA POOLS - ARCHIVE V3
 * ====================================================================================================
 * CONFIGURACIÓN DE ALTA GAMA: Banco de contenido bilingüe aleatorio para erradicar la monotonía.
 * Cruza estados de saturación mental con enrutamientos físicos de ultra-lujo (IATA BNT Compatible).
 */

const RAW_RIDDLES_DATABASE = [
    {
        id: "ADV-001",
        es: "No tengo voz y te dicto verdades, te sigo en el lujo y en las soledades. Si el ruido del mundo te causa ceguera, mi abrazo te muestra tu paz verdadera. ¿Qué soy?",
        en: "I have no voice yet I dictate truths, I follow you in luxury and in solitude. If the world's noise blinds your path, my embrace shows your true peace. What am I?",
        ans_es: "Silencio",
        ans_en: "Silence"
    },
    {
        id: "ADV-002",
        es: "Nazco en la uva, maduro en la sombra, acompaño al rey cuando el oro lo nombra. Desato lenguajes, detengo el apuro, y curo el cansancio de un día maduro. ¿Qué soy?",
        en: "Born in the grape, aged in the dark, I accompany kings when gold leaves its mark. I unchain long talks, I slow down the race, and heal the fatigue of a hard day's pace. What am I?",
        ans_es: "Vino",
        ans_en: "Wine"
    },
    {
        id: "ADV-003",
        es: "Bajo tu cama o en alta montaña, mi manto de hilos el tiempo acompaña. Te obligo a parar si te encuentras perdido, y sano la mente del cuerpo fundido. ¿Qué soy?",
        en: "Under your bed or on peaks grand and high, my blanket of threads watches seasons pass by. I force you to pause if you're losing your way, and heal the exhaustion of a chaotic day. What am I?",
        ans_es: "Descanso",
        ans_en: "Rest"
    },
    {
        id: "ADV-005", // 🚨 REQUISITO CRÍTICO: Utilizada por el script en el Reto del Minuto 1
        id_ref: "RESPIRACION_CONSOLIDACION",
        es: "Invisible al ojo, vital para el alma, si me dejas ir te devuelvo la calma. Me muevo en tu pecho sin prisa ni daño, y rompo el estrés de todo tu año. ¿Qué soy?",
        en: "Invisible to eyes, vital to the soul, if you let me flow I make your mind whole. I move in your chest with absolute grace, breaking the patterns of your routine's race. What am I?",
        ans_es: "Respiración",
        ans_en: "Breathing"
    }
];

const RAW_HOTELS_INVENTORY = [
    {
        id: "HOT-ELITE-001",
        name_es: "Eden Roc Cap Cana — República Dominicana",
        name_en: "Eden Roc Cap Cana — Dominican Republic",
        tier: "ELITE",
        vibe: "Naturaleza y Océano",
        desc_es: "Villas privadas con piscina propia y acceso exclusivo a un enclave de arena blanca libre de ruido corporativo.",
        desc_en: "Private beachfront villas with plunge pools and exclusive access to a pristine white-sand enclave free from corporate noise."
    },
    {
        id: "HOT-ELITE-002",
        name_es: "Amanera Playa Grande — República Dominicana",
        name_en: "Amanera Playa Grande — Dominican Republic",
        tier: "ELITE",
        vibe: "Aislamiento Total",
        desc_es: "Casitas de diseño minimalista zen suspendidas sobre acantilados de la selva virgen del Caribe con silencio acústico absoluto.",
        desc_en: "Minimalist Zen casitas suspended over wild Caribbean jungle cliffs, providing absolute acoustic silence."
    },
    {
        id: "HOT-PREM-001",
        name_es: "Chablé Maroma — Riviera Maya, México",
        name_en: "Chablé Maroma — Riviera Maya, Mexico",
        tier: "PREMIUM",
        vibe: "Purificación",
        desc_es: "Santuario maya oculto en la selva, famoso por su spa holístico de alta gama y rituales de desintoxicación energética.",
        desc_en: "Hidden Mayan sanctuary in the jungle, famous for its high-end holistic spa and energy detox rituals."
    }
];

const RAW_TRANSPORTS_INVENTORY = [
    {
        id: "TRA-ELITE-AIR01",
        type: "AVIACION",
        tier: "ELITE",
        desc_es: "Vuelo Privado en Gulfstream G650 con catering gourmet de autor y salida desde terminales VIP ejecutivas sin filas.",
        desc_en: "Private Gulfstream G650 Flight featuring signature gourmet catering and departure from hassle-free private VIP terminals."
    },
    {
        id: "TRA-ELITE-SEA01",
        type: "CRUCERO",
        tier: "ELITE",
        desc_es: "Travesía Premium en The Ritz-Carlton Yacht Collection alojado en suite ejecutiva con terraza privada sobre el agua.",
        desc_en: "Premium voyage on The Ritz-Carlton Yacht Collection accommodated in an executive private waterfront terrace suite."
    }
];

const RESPIRATION_COUNSELING_SCRIPTS = {
    MATUTINO: {
        pattern: "3-1-3-0",
        frases_es: [
            "Inhala el aire fresco del amanecer... Siente la energía limpia entrar.",
            "Retén un segundo... Tu mente toma el control de tu día.",
            "Exhala el residuo del cansancio acumulado... Suelta la rigidez.",
            "Pausa... Tu sistema autónomo se calibra de forma óptima."
        ],
        frases_en: [
            "Inhale the crisp morning air... Feel clean energy entering your core.",
            "Hold for a second... Your mind commands complete control over the day.",
            "Exhale the residual friction of routine... Release all tightness.",
            "Pause... Your autonomous system calibrates to its optimal state."
        ]
    },
    MIDDAY: {
        pattern: "4-4-4-4",
        frases_es: [
            "Inhala profundamente estabilizando el ritmo cardíaco...",
            "Retén el aire, suspendiendo las cargas y el ruido externo...",
            "Exhala liberando la tensión acumulada en tus hombros...",
            "Pausa en vacío, permitiendo que tu enfoque recupere claridad."
        ],
        frases_en: [
            "Inhale deeply, stabilizing your heart rate rhythm...",
            "Hold the breath, suspending external noise and burdens...",
            "Exhale, releasing accumulated tension from your shoulders...",
            "Pause in stillness, allowing your focus to regain absolute clarity."
        ]
    },
    NOCTURNO: {
        pattern: "4-7-8",
        frases_es: [
            "Inhala profundamente desactivando la alerta del cerebro...",
            "Retén el aire... Deja que la quietud reemplace las tareas pendientes.",
            "Exhala lento, vaciando por completo la saturación digital...",
            "Siente cómo tu cuerpo se funde en un estado de desconexión total."
        ],
        frases_en: [
            "Inhale deeply, shutting down your brain's alert pathways...",
            "Hold the breath... Let profound stilleness replace pending tasks.",
            "Exhale slowly, completely emptying all digital saturation...",
            "Feel your entire body melting into a state of total disconnection."
        ]
    }
};
