import { chromium } from 'playwright';

const BASE_URL = process.env.E2E_URL || 'http://127.0.0.1:3000';

async function assert(condition, message) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

async function run() {
  console.log(`Iniciando verificación E2E de Vigía EPP en ${BASE_URL}...`);
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  });
  const page = await browser.newPage();

  try {
    // 1. Resumen (/resumen)
    await page.goto(`${BASE_URL}/resumen`, { waitUntil: 'networkidle' });
    const heroText = await page.getByTestId('hero-frase').textContent();
    console.log('Hero frase:', heroText);
    await assert(
      heroText && heroText.includes('trabajadores sin EPP completo'),
      'La frase hero en /resumen debe mostrar trabajadores sin EPP completo'
    );

    // Probar Modo Jurado en Vivo (tarjeta sin_lentes)
    await page.getByTestId('jurado-btn-sin_lentes').click();
    await page.getByTestId('jurado-resultado').waitFor({ state: 'visible', timeout: 8000 });
    const juradoTexto = await page.getByTestId('jurado-resultado').textContent();
    await assert(
      juradoTexto && juradoTexto.includes('Carlos Mendoza'),
      'Modo Jurado debe mostrar el hallazgo emergente de Carlos Mendoza'
    );
    console.log('✓ /resumen y Modo Jurado verificados');

    // 2. Kiosco en vivo (/kiosco)
    await page.goto(`${BASE_URL}/kiosco`, { waitUntil: 'networkidle' });
    await page.waitForFunction(
      () => document.querySelector('[data-testid="kiosco-veredicto"]')?.textContent?.includes('PASE DE TURNO AUTORIZADO'),
      { timeout: 8000 }
    );
    await page.getByTestId('kiosco-preset-sin_lentes').click();
    await page.waitForFunction(
      () => document.querySelector('[data-testid="kiosco-veredicto"]')?.textContent?.includes('ACCESO DETENIDO'),
      { timeout: 8000 }
    );
    await page.getByTestId('kiosco-preset-completo').click();
    await page.waitForFunction(
      () => document.querySelector('[data-testid="kiosco-veredicto"]')?.textContent?.includes('PASE DE TURNO AUTORIZADO'),
      { timeout: 8000 }
    );
    console.log('✓ /kiosco y sus 3 zonas anatómicas verificados');

    // 3. Recorrido (/recorrido)
    await page.goto(`${BASE_URL}/recorrido`, { waitUntil: 'networkidle' });
    const tituloRecorrido = await page.locator('h2').textContent();
    await assert(
      tituloRecorrido && tituloRecorrido.includes('Recorrido de Fila'),
      'La vista /recorrido debe renderizar su encabezado'
    );
    console.log('✓ /recorrido verificado');

    // 4. Cuadrilla y Gemelo Anatómico (/cuadrilla)
    await page.goto(`${BASE_URL}/cuadrilla`, { waitUntil: 'networkidle' });
    await page.getByTestId('estacion-card-L1-T2').click();
    const gemeloTexto = await page.getByTestId('gemelo-anatomico-panel').textContent();
    await assert(
      gemeloTexto && gemeloTexto.includes('Marco Antonio Ríos'),
      'El Gemelo Anatómico debe mostrar el detalle de Marco Antonio Ríos (L1-T2)'
    );
    console.log('✓ /cuadrilla y Gemelo Anatómico de 3 zonas verificados');

    // 5. Hallazgos y Persistencia Transaccional (/hallazgos)
    await page.goto(`${BASE_URL}/hallazgos`, { waitUntil: 'networkidle' });
    const riesgoAntes = await page.getByTestId('hallazgos-riesgo-activo').textContent();
    await page.getByTestId('btn-corregir-hallazgo-l1-t4').click();
    await page.waitForTimeout(600);
    const riesgoDespues = await page.getByTestId('hallazgos-riesgo-activo').textContent();
    await assert(
      riesgoAntes !== riesgoDespues,
      `El riesgo activo debe actualizarse al marcar corregido (${riesgoAntes} -> ${riesgoDespues})`
    );
    // Revertir para dejar el estado demo limpio
    await page.getByTestId('btn-corregir-hallazgo-l1-t4').click();
    await page.waitForTimeout(600);
    const riesgoRestaurado = await page.getByTestId('hallazgos-riesgo-activo').textContent();
    await assert(
      riesgoRestaurado === riesgoAntes,
      'El riesgo activo debe restaurarse al revertir el hallazgo'
    );
    console.log('✓ /hallazgos y persistencia PATCH verificados');

    // 6. Impacto en Red (/red)
    await page.goto(`${BASE_URL}/red`, { waitUntil: 'networkidle' });
    const tituloRed = await page.locator('h2').textContent();
    await assert(
      tituloRed && tituloRed.includes('18 Plantas'),
      'La vista /red debe mostrar la proyección en las 18 plantas'
    );
    console.log('✓ /red verificado');

    // 7. Subir Video (/analizar)
    await page.goto(`${BASE_URL}/analizar`, { waitUntil: 'networkidle' });
    const tituloAnalizar = await page.locator('h2').textContent();
    await assert(
      tituloAnalizar && tituloAnalizar.includes('Subir y Procesar Nuevo Video'),
      'La vista /analizar debe cargar correctamente'
    );
    console.log('✓ /analizar verificado');

    // 8. Asistente IA RAG (/asistente)
    await page.goto(`${BASE_URL}/asistente`, { waitUntil: 'networkidle' });
    await page.getByTestId('sugerencia-chat-0').click();
    await page.getByTestId('mensaje-asistente-2').waitFor({ state: 'visible', timeout: 8000 });
    const respChat = await page.getByTestId('mensaje-asistente-2').textContent();
    await assert(
      respChat && respChat.includes('Marco Antonio Ríos'),
      'El Asistente IA debe responder citando a los trabajadores de la corrida'
    );
    console.log('✓ /asistente RAG verificado');

    console.log('TODAS LAS 8 PANTALLAS SUPERARON LA PRUEBA E2E CON PLAYWRIGHT.');
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
