// Spanish / English texts for the whole game.

export const LANGS = ['es', 'en'];

const STRINGS = {
  es: {
    title: 'Loci',
    subtitle: 'El Palacio de la Memoria',
    tagline: 'Recorre un palacio, deja en él imágenes imposibles de olvidar y descubre cuánto puede recordar tu mente.',
    play: 'Entrar al palacio',
    difficulty: 'Dificultad',
    easy: 'Fácil',
    normal: 'Normal',
    hard: 'Difícil',
    objects: 'objetos',
    quality: 'Calidad gráfica',
    q_low: 'Baja',
    q_medium: 'Media',
    q_high: 'Alta',
    language: 'Idioma',
    best: 'Mejor marca',
    none: '—',
    howto_title: 'Cómo se juega',
    howto: [
      'El <b>método de los loci</b> es una técnica de memoria usada desde la antigua Grecia: asocias cada cosa que quieres recordar a un lugar concreto de un edificio que conoces bien.',
      '<b>1. Memoriza.</b> Recibirás una lista de objetos en orden. Recorre el palacio siguiendo la luz dorada y coloca cada objeto en su lugar. Imagina la escena: cuanto más absurda y vívida, mejor.',
      '<b>2. Recuerda.</b> Los objetos desaparecen. Vuelve a recorrer el palacio y, en cada lugar, elige el objeto que dejaste allí.',
    ],
    controls_title: 'Controles',
    controls: [
      ['Ratón', 'Mirar'],
      ['W A S D / flechas', 'Caminar'],
      ['Mayús', 'Correr'],
      ['E / clic', 'Interactuar'],
      ['Esc', 'Pausa'],
    ],
    loading: 'Construyendo el palacio…',
    intro_title: 'Tu lista',
    intro_text: 'Memoriza estos {n} objetos <b>en este orden</b>. Los irás dejando, uno a uno, en los lugares del palacio.',
    intro_go: 'Empezar el recorrido',
    click_to_play: 'Haz clic para continuar',
    phase_memorize: 'Memoriza',
    phase_recall: 'Recuerda',
    phase_review: 'Recorrido final',
    place_prompt: 'Colocar {item} en {place}',
    recall_prompt: '¿Qué dejaste en {place}?',
    recall_change: 'Cambiar lo que pusiste en {place}',
    follow_light: 'Sigue la luz dorada hasta el siguiente lugar',
    imagine: 'Imagina',
    all_placed_title: 'Todo está en su sitio',
    all_placed_text: 'Recorre el palacio una vez más para fijar las imágenes. Cuando estés listo, pulsa <kbd>R</kbd> para empezar a recordar.',
    ready_prompt: 'Pulsa R para empezar a recordar',
    recall_intro_title: 'Hora de recordar',
    recall_intro_text: 'Los objetos se han desvanecido. Vuelve a recorrer el palacio desde la entrada y, en cada lugar marcado, elige lo que dejaste allí.',
    recall_go: 'Recorrer de nuevo',
    choose_title: '¿Qué había en {place}?',
    cancel: 'Cancelar',
    answered: 'Respondidos',
    finish: 'Terminar',
    finish_prompt: 'Pulsa F para terminar',
    results_title: 'Resultados',
    results_score: 'Has recordado {c} de {n} objetos',
    time_memorize: 'Tiempo memorizando',
    time_recall: 'Tiempo recordando',
    col_place: 'Lugar',
    col_answer: 'Tu respuesta',
    col_correct: 'Correcto',
    new_record: '¡Nuevo récord!',
    play_again: 'Jugar otra vez',
    walk_review: 'Pasear por el palacio',
    menu: 'Menú principal',
    paused: 'Pausa',
    resume: 'Continuar',
    restart: 'Reiniciar partida',
    end_review: 'Volver a los resultados',
    rank: ['Sigue entrenando', 'Buena memoria', 'Memoria de orador', 'Maestro de los loci'],
    webgl_error: 'Tu navegador no admite WebGL 2, necesario para mostrar el palacio en 3D.',
    desktop_hint: 'Este juego necesita teclado y ratón.',
  },
  en: {
    title: 'Loci',
    subtitle: 'The Memory Palace',
    tagline: 'Walk through a palace, leave unforgettable images in it and find out how much your mind can hold.',
    play: 'Enter the palace',
    difficulty: 'Difficulty',
    easy: 'Easy',
    normal: 'Normal',
    hard: 'Hard',
    objects: 'objects',
    quality: 'Graphics quality',
    q_low: 'Low',
    q_medium: 'Medium',
    q_high: 'High',
    language: 'Language',
    best: 'Best score',
    none: '—',
    howto_title: 'How to play',
    howto: [
      'The <b>method of loci</b> is a memory technique used since ancient Greece: you tie each thing you want to remember to a specific place in a building you know well.',
      '<b>1. Memorize.</b> You get a list of objects in order. Walk through the palace following the golden light and put each object in its place. Picture the scene: the more absurd and vivid, the better.',
      '<b>2. Recall.</b> The objects vanish. Walk the palace again and, at each place, choose the object you left there.',
    ],
    controls_title: 'Controls',
    controls: [
      ['Mouse', 'Look'],
      ['W A S D / arrows', 'Walk'],
      ['Shift', 'Run'],
      ['E / click', 'Interact'],
      ['Esc', 'Pause'],
    ],
    loading: 'Building the palace…',
    intro_title: 'Your list',
    intro_text: 'Memorize these {n} objects <b>in this order</b>. You will leave them, one by one, in the places of the palace.',
    intro_go: 'Start the walk',
    click_to_play: 'Click to continue',
    phase_memorize: 'Memorize',
    phase_recall: 'Recall',
    phase_review: 'Final walk',
    place_prompt: 'Place {item} on {place}',
    recall_prompt: 'What did you leave on {place}?',
    recall_change: 'Change what you put on {place}',
    follow_light: 'Follow the golden light to the next place',
    imagine: 'Imagine',
    all_placed_title: 'Everything is in place',
    all_placed_text: 'Walk the palace once more to fix the images. When you are ready, press <kbd>R</kbd> to start recalling.',
    ready_prompt: 'Press R to start recalling',
    recall_intro_title: 'Time to remember',
    recall_intro_text: 'The objects have faded away. Walk the palace again from the entrance and, at each marked place, choose what you left there.',
    recall_go: 'Walk again',
    choose_title: 'What was on {place}?',
    cancel: 'Cancel',
    answered: 'Answered',
    finish: 'Finish',
    finish_prompt: 'Press F to finish',
    results_title: 'Results',
    results_score: 'You remembered {c} of {n} objects',
    time_memorize: 'Time memorizing',
    time_recall: 'Time recalling',
    col_place: 'Place',
    col_answer: 'Your answer',
    col_correct: 'Correct',
    new_record: 'New record!',
    play_again: 'Play again',
    walk_review: 'Walk the palace',
    menu: 'Main menu',
    paused: 'Paused',
    resume: 'Resume',
    restart: 'Restart game',
    end_review: 'Back to results',
    rank: ['Keep training', 'Good memory', 'Orator\'s memory', 'Master of loci'],
    webgl_error: 'Your browser does not support WebGL 2, which is needed to show the palace in 3D.',
    desktop_hint: 'This game needs a keyboard and mouse.',
  },
};

const ROOMS = {
  es: { vestibule: 'Vestíbulo', library: 'Biblioteca', courtyard: 'Patio', gallery: 'Galería de pinturas', hall: 'Salón del trono' },
  en: { vestibule: 'Vestibule', library: 'Library', courtyard: 'Courtyard', gallery: 'Picture gallery', hall: 'Throne hall' },
};

const PLACES = {
  es: {
    pedestal: 'el pedestal de mármol',
    round_table: 'la mesa redonda',
    console: 'la consola dorada',
    reading_table: 'la mesa de lectura',
    lectern: 'el atril',
    side_table: 'la mesita del rincón',
    bench: 'el banco de piedra',
    fountain: 'la fuente',
    sundial: 'el reloj de sol',
    pedestal_south: 'el pedestal junto a los cuadros',
    ottoman: 'el banco de terciopelo',
    pedestal_north: 'el pedestal verde',
    banquet_table: 'la mesa del banquete',
    altar: 'el altar',
    throne: 'el trono',
  },
  en: {
    pedestal: 'the marble pedestal',
    round_table: 'the round table',
    console: 'the gilded console',
    reading_table: 'the reading table',
    lectern: 'the lectern',
    side_table: 'the corner side table',
    bench: 'the stone bench',
    fountain: 'the fountain',
    sundial: 'the sundial',
    pedestal_south: 'the pedestal by the paintings',
    ottoman: 'the velvet bench',
    pedestal_north: 'the green pedestal',
    banquet_table: 'the banquet table',
    altar: 'the altar',
    throne: 'the throne',
  },
};

// name, name with article, vivid image ({place} is replaced)
const ITEMS = {
  es: {
    apple: ['Manzana', 'la manzana', 'Una manzana gigante y brillante rueda sobre {place} dejando un rastro de zumo pegajoso que huele a otoño.'],
    key: ['Llave', 'la llave', 'Una llave dorada del tamaño de un brazo gira sola en el aire sobre {place}, abriendo cerraduras invisibles con un clic metálico.'],
    book: ['Libro', 'el libro', 'Un libro antiguo se abre de golpe en {place} y de sus páginas salen volando cientos de letras como mariposas.'],
    candle: ['Vela', 'la vela', 'Una vela enorme arde en {place}; su cera gotea como una cascada y su llama canta en voz baja.'],
    crown: ['Corona', 'la corona', 'Una corona real descansa en {place}, tan pesada que hunde la madera y sus gemas lanzan destellos que te ciegan.'],
    hourglass: ['Reloj de arena', 'el reloj de arena', 'Un reloj de arena en {place} derrama arena dorada sin parar, formando una duna que te llega a los tobillos.'],
    sword: ['Espada', 'la espada', 'Una espada legendaria está clavada en {place} y vibra con un zumbido grave cuando te acercas.'],
    bell: ['Campana', 'la campana', 'Una campana de bronce repica sola en {place}, tan fuerte que tiemblan los cristales de todo el palacio.'],
    amphora: ['Ánfora', 'el ánfora', 'Un ánfora griega en {place} rebosa vino tinto que se derrama en espiral por el suelo.'],
    chalice: ['Cáliz', 'el cáliz', 'Un cáliz de oro en {place} brilla como un pequeño sol y de él brota una fuente de agua cristalina.'],
    anchor: ['Ancla', 'el ancla', 'Un ancla de barco oxidada ha caído sobre {place}, todavía chorreando agua de mar y algas.'],
    globe: ['Globo terráqueo', 'el globo terráqueo', 'Un globo terráqueo gira a toda velocidad en {place} y por sus océanos navegan barquitos diminutos.'],
    lantern: ['Farol', 'el farol', 'Un farol de hierro cuelga sobre {place} y su luz proyecta en las paredes sombras de animales que se mueven.'],
    mushroom: ['Seta', 'la seta', 'Una seta roja con lunares blancos crece de golpe en {place} hasta hacerse tan grande como un paraguas.'],
    ring: ['Anillo', 'el anillo', 'Un anillo con un rubí enorme flota sobre {place}, girando y lanzando reflejos rojos como un faro.'],
    dice: ['Dado', 'el dado', 'Un dado gigante cae con estruendo sobre {place}, rebota tres veces y siempre sale un seis.'],
    teapot: ['Tetera', 'la tetera', 'Una tetera de porcelana silba en {place} y lanza nubes de vapor con olor a menta.'],
    horseshoe: ['Herradura', 'la herradura', 'Una herradura al rojo vivo chisporrotea en {place}, como si un caballo invisible acabara de perderla.'],
    pear: ['Pera', 'la pera', 'Una pera madura en {place} se balancea sola como un tentetieso y suelta una risita cada vez que la miras.'],
    hammer: ['Martillo', 'el martillo', 'Un martillo golpea {place} una y otra vez, ¡pum, pum, pum!, haciendo saltar chispas en cada golpe.'],
  },
  en: {
    apple: ['Apple', 'the apple', 'A giant shiny apple rolls across {place}, leaving a sticky trail of juice that smells of autumn.'],
    key: ['Key', 'the key', 'A golden key as long as your arm spins in the air above {place}, unlocking invisible locks with a metallic click.'],
    book: ['Book', 'the book', 'An ancient book bursts open on {place} and hundreds of letters fly out of its pages like butterflies.'],
    candle: ['Candle', 'the candle', 'A huge candle burns on {place}; its wax pours like a waterfall and its flame hums softly.'],
    crown: ['Crown', 'the crown', 'A royal crown rests on {place}, so heavy it dents the wood, its gems flashing bright enough to blind you.'],
    hourglass: ['Hourglass', 'the hourglass', 'An hourglass on {place} pours golden sand endlessly, building a dune up to your ankles.'],
    sword: ['Sword', 'the sword', 'A legendary sword is stuck into {place} and hums with a deep buzz as you approach.'],
    bell: ['Bell', 'the bell', 'A bronze bell rings by itself on {place}, so loud that every window in the palace shakes.'],
    amphora: ['Amphora', 'the amphora', 'A Greek amphora on {place} overflows with red wine that spirals across the floor.'],
    chalice: ['Chalice', 'the chalice', 'A golden chalice on {place} glows like a small sun while crystal-clear water fountains out of it.'],
    anchor: ['Anchor', 'the anchor', 'A rusty ship\'s anchor has crashed onto {place}, still dripping seawater and seaweed.'],
    globe: ['Globe', 'the globe', 'A globe spins at full speed on {place} while tiny ships sail across its oceans.'],
    lantern: ['Lantern', 'the lantern', 'An iron lantern hangs over {place}, casting shadows of animals that move along the walls.'],
    mushroom: ['Mushroom', 'the mushroom', 'A red mushroom with white spots sprouts on {place} and grows as big as an umbrella.'],
    ring: ['Ring', 'the ring', 'A ring with an enormous ruby floats above {place}, spinning and flashing red like a lighthouse.'],
    dice: ['Die', 'the die', 'A giant die crashes onto {place}, bounces three times and always lands on six.'],
    teapot: ['Teapot', 'the teapot', 'A porcelain teapot whistles on {place}, puffing clouds of mint-scented steam.'],
    horseshoe: ['Horseshoe', 'the horseshoe', 'A red-hot horseshoe sizzles on {place}, as if an invisible horse had just lost it.'],
    pear: ['Pear', 'the pear', 'A ripe pear on {place} wobbles by itself like a roly-poly toy and giggles whenever you look at it.'],
    hammer: ['Hammer', 'the hammer', 'A hammer pounds {place} again and again, bang, bang, bang, sending sparks flying with every blow.'],
  },
};

let lang = 'es';

export function detectLang() {
  try {
    const saved = localStorage.getItem('loci.lang');
    if (LANGS.includes(saved)) return saved;
  } catch { /* storage unavailable */ }
  return (navigator.language || 'es').toLowerCase().startsWith('es') ? 'es' : 'en';
}

export function setLang(l) {
  lang = LANGS.includes(l) ? l : 'es';
  document.documentElement.lang = lang;
  try { localStorage.setItem('loci.lang', lang); } catch { /* ignore */ }
}

export function getLang() {
  return lang;
}

export function t(key, vars = {}) {
  let s = STRINGS[lang][key] ?? STRINGS.es[key] ?? key;
  if (typeof s === 'string') {
    for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, v);
  }
  return s;
}

export const roomName = (id) => ROOMS[lang][id] ?? id;
export const placeName = (id) => PLACES[lang][id] ?? id;
export const itemName = (id) => ITEMS[lang][id][0];
export const itemWithArticle = (id) => ITEMS[lang][id][1];
export const itemImage = (id, place) => ITEMS[lang][id][2].replaceAll('{place}', place);
export const ITEM_IDS = Object.keys(ITEMS.es);
