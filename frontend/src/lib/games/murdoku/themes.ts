import type { PropIcon } from './types.ts';

export interface ThemeProp {
	name: string;
	icon: PropIcon;
}

/** Escenario del caso: títulos, habitaciones y objetos en español neutro. */
export interface MurdokuTheme {
	key: string;
	setting: string;
	titles: readonly string[];
	regions: readonly string[];
	props: readonly ThemeProp[];
}

/**
 * Ocho escenarios con ocho títulos cada uno: los 62 casos del catálogo usan cada
 * título una sola vez. Las regiones se recortan a 4–6 por caso.
 */
export const MURDOKU_THEMES: readonly MurdokuTheme[] = [
	{
		key: 'studio',
		setting: 'Una mansión a medianoche',
		titles: [
			'El estudio',
			'La chimenea del estudio',
			'Medianoche en el estudio',
			'El sillón vacío',
			'La puerta del estudio',
			'Un piano desafinado',
			'Polvo en el piano',
			'El retrato del estudio'
		],
		regions: ['Estudio', 'Biblioteca', 'Pasillo', 'Cocina', 'Jardín', 'Terraza'],
		props: [
			{ name: 'piano', icon: 'piano' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'estantería', icon: 'shelf' },
			{ name: 'cuadro', icon: 'painting' },
			{ name: 'planta', icon: 'plant' },
			{ name: 'baúl', icon: 'chest' },
			{ name: 'estatua', icon: 'statue' },
			{ name: 'retrato', icon: 'painting' },
			{ name: 'candelabro', icon: 'lamp' }
		]
	},
	{
		key: 'library',
		setting: 'Una biblioteca cerrada al público',
		titles: [
			'La biblioteca',
			'El atlas abierto',
			'Silencio en la biblioteca',
			'La escala prohibida',
			'El catálogo roto',
			'Última consulta',
			'La sala de mapas',
			'El libro devuelto'
		],
		regions: ['Vestíbulo', 'Galería', 'Sala de lectura', 'Depósito', 'Patio', 'Torre'],
		props: [
			{ name: 'estantería', icon: 'shelf' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'busto', icon: 'statue' },
			{ name: 'cuadro', icon: 'painting' },
			{ name: 'planta', icon: 'plant' },
			{ name: 'cofre', icon: 'chest' },
			{ name: 'atril', icon: 'shelf' },
			{ name: 'candelabro', icon: 'lamp' },
			{ name: 'estatua', icon: 'statue' }
		]
	},
	{
		key: 'greenhouse',
		setting: 'Un invernadero al amanecer',
		titles: [
			'El invernadero',
			'La orquídea negra',
			'Rocío en el invernadero',
			'La maceta volcada',
			'El cristal empañado',
			'Flores de medianoche',
			'La regadera olvidada',
			'Un tallo quebrado'
		],
		regions: ['Invernadero', 'Orangerie', 'Fuente', 'Rosaleda', 'Taller', 'Cobertizo'],
		props: [
			{ name: 'helecho', icon: 'plant' },
			{ name: 'maceta', icon: 'plant' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'estatua', icon: 'statue' },
			{ name: 'arcón', icon: 'chest' },
			{ name: 'estantería', icon: 'shelf' },
			{ name: 'cuadro', icon: 'painting' },
			{ name: 'piano', icon: 'piano' },
			{ name: 'candelabro', icon: 'lamp' }
		]
	},
	{
		key: 'kitchen',
		setting: 'Una cocina de servicio en plena cena',
		titles: [
			'La cocina de servicio',
			'El cuchillo del pan',
			'La cena interrumpida',
			'Vapor en la despensa',
			'El horno encendido',
			'La mesa sin postre',
			'La despensa abierta',
			'Café a medianoche'
		],
		regions: ['Cocina', 'Despensa', 'Comedor', 'Office', 'Patio', 'Bodega'],
		props: [
			{ name: 'aparador', icon: 'shelf' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'baúl', icon: 'chest' },
			{ name: 'planta aromática', icon: 'plant' },
			{ name: 'bodegón', icon: 'painting' },
			{ name: 'figura', icon: 'statue' },
			{ name: 'estantería', icon: 'shelf' },
			{ name: 'candelabro', icon: 'lamp' },
			{ name: 'piano', icon: 'piano' }
		]
	},
	{
		key: 'museum',
		setting: 'Un museo después del cierre',
		titles: [
			'El museo',
			'La vitrina vacía',
			'Después del cierre',
			'La sala egipcia',
			'El mármol roto',
			'Una sombra en el pasillo',
			'El inventario incompleto',
			'La sala griega al alba'
		],
		regions: ['Vestíbulo', 'Sala egipcia', 'Sala griega', 'Depósito', 'Taller', 'Patio'],
		props: [
			{ name: 'estatua', icon: 'statue' },
			{ name: 'busto', icon: 'statue' },
			{ name: 'cuadro', icon: 'painting' },
			{ name: 'vitrina', icon: 'shelf' },
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'cofre', icon: 'chest' },
			{ name: 'planta', icon: 'plant' },
			{ name: 'retrato', icon: 'painting' },
			{ name: 'estantería', icon: 'shelf' }
		]
	},
	{
		key: 'train',
		setting: 'Un tren nocturno detenido',
		titles: [
			'El tren nocturno',
			'El vagón restaurante',
			'La litera nueve',
			'El andén sin luces',
			'Un freno de emergencia',
			'El último silbato',
			'Una maleta sin dueño',
			'El coche de correo'
		],
		regions: ['Vagón restaurante', 'Vagón litera', 'Pasillo', 'Furgón', 'Cabina', 'Andén'],
		props: [
			{ name: 'maleta', icon: 'chest' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'estantería', icon: 'shelf' },
			{ name: 'planta', icon: 'plant' },
			{ name: 'cuadro', icon: 'painting' },
			{ name: 'piano', icon: 'piano' },
			{ name: 'estatua', icon: 'statue' },
			{ name: 'candelabro', icon: 'lamp' },
			{ name: 'baúl', icon: 'chest' }
		]
	},
	{
		key: 'lighthouse',
		setting: 'Un faro aislado por la tormenta',
		titles: [
			'El faro',
			'La tormenta en el faro',
			'La lámpara apagada',
			'El mar embravecido',
			'La escalera de caracol',
			'Luces en la niebla',
			'Marea baja',
			'El faro sin guardia'
		],
		regions: ['Sala de máquinas', 'Escalera', 'Cocina', 'Dormitorio', 'Terraza', 'Muelle'],
		props: [
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'baúl', icon: 'chest' },
			{ name: 'planta', icon: 'plant' },
			{ name: 'cuadro', icon: 'painting' },
			{ name: 'estantería', icon: 'shelf' },
			{ name: 'estatua', icon: 'statue' },
			{ name: 'piano', icon: 'piano' },
			{ name: 'candelabro', icon: 'lamp' },
			{ name: 'busto', icon: 'statue' }
		]
	},
	{
		key: 'theatre',
		setting: 'Un teatro después de la función',
		titles: [
			'El teatro',
			'La función terminó',
			'El palco abandonado',
			'Telón abajo',
			'El camerino vacío',
			'Aplausos de medianoche',
			'La tramoya a oscuras',
			'El vestuario de utilería'
		],
		regions: ['Escenario', 'Platea', 'Palco', 'Camerinos', 'Vestíbulo', 'Tramoya'],
		props: [
			{ name: 'piano', icon: 'piano' },
			{ name: 'lámpara', icon: 'lamp' },
			{ name: 'cuadro', icon: 'painting' },
			{ name: 'baúl', icon: 'chest' },
			{ name: 'estatua', icon: 'statue' },
			{ name: 'planta', icon: 'plant' },
			{ name: 'reloj', icon: 'clock' },
			{ name: 'estantería', icon: 'shelf' },
			{ name: 'candelabro', icon: 'lamp' },
			{ name: 'retrato', icon: 'painting' }
		]
	}
];
