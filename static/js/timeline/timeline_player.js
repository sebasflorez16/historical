/**
 * 🎬 Timeline Player para AgroTech Histórico
 * Reproductor visual de evolución temporal de datos satelitales
 * 
 * @author AgroTech Team
 * @version 1.0.0
 */

class TimelinePlayer {
    constructor(config) {
        this.config = config;
        this.canvas = document.getElementById(config.canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Datos del timeline
        this.frames = [];
        this.currentIndex = 0;
        this.currentIndice = 'ndvi'; // ndvi, ndmi, savi
        
        // Estado de reproducción
        this.isPlaying = false;
        this.playInterval = null;
        this.playSpeed = 8000; // ms por frame (más tiempo para análisis)
        
        // Caché de imágenes
        this.imageCache = new Map();
        this.loadingImages = new Set();
        
        // Elementos del DOM
        this.elements = {};
        
        // Sistema de transiciones
        this.transition = {
            active: false,
            progress: 1,
            fromFrame: null,
            toFrame: null,
            startTime: 0,
            duration: 1200,  // ms de transición (más largo para suavidad)
            animationId: null
        };
        
        // Bind methods
        this.play = this.play.bind(this);
        this.pause = this.pause.bind(this);
        this.next = this.next.bind(this);
        this.prev = this.prev.bind(this);
        this.goToFrame = this.goToFrame.bind(this);
        this.changeIndice = this.changeIndice.bind(this);
        this.animateTransition = this.animateTransition.bind(this);
    }
    
    /**
     * Inicializa el player
     */
    async init() {
        console.log('🎬 Inicializando Timeline Player...');
        
        // Configurar canvas
        this.setupCanvas();
        
        // Obtener referencias a elementos del DOM
        this.setupElements();
        
        // Configurar event listeners
        this.setupEventListeners();
        
        // Cargar datos del timeline
        await this.loadTimelineData();
        
        // Renderizar primer frame
        if (this.frames.length > 0) {
            await this.renderFrame(0);
        }
        
        console.log('✅ Timeline Player inicializado correctamente');
    }
    
    /**
     * Configura el canvas
     */
    setupCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        
        // Fondo inicial
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
    
    /**
     * Obtiene referencias a elementos del DOM
     */
    setupElements() {
        this.elements = {
            // Controles
            btnPlay: document.getElementById('btn-play'),
            btnPrev: document.getElementById('btn-prev'),
            btnNext: document.getElementById('btn-next'),
            btnFirst: document.getElementById('btn-first'),
            btnLast: document.getElementById('btn-last'),
            slider: document.getElementById('timeline-slider'),
            frameCounter: document.getElementById('frame-counter'),
            
            // Metadata
            iconPeriodo: document.getElementById('icon-periodo'),
            valuePeriodo: document.getElementById('value-periodo'),
            iconIndice: document.getElementById('icon-indice'),
            valueIndice: document.getElementById('value-indice'),
            iconTendencia: document.getElementById('icon-tendencia'),
            valueTendencia: document.getElementById('value-tendencia'),
            iconCalidad: document.getElementById('icon-calidad'),
            valueCalidad: document.getElementById('value-calidad'),
            resumenSimple: document.getElementById('resumen-simple'),
            
            // Selector de índice
            indexButtons: document.querySelectorAll('.index-btn'),
            
            // Botones de descarga
            btnDownloadNdvi: document.getElementById('btn-download-ndvi'),
            btnDownloadNdmi: document.getElementById('btn-download-ndmi'),
            btnDownloadSavi: document.getElementById('btn-download-savi'),
            
            // Loading
            loadingOverlay: document.getElementById('loading-overlay')
        };
    }
    
    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Controles de reproducción
        this.elements.btnPlay.addEventListener('click', () => {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        });
        
        this.elements.btnPrev.addEventListener('click', this.prev);
        this.elements.btnNext.addEventListener('click', this.next);
        
        this.elements.btnFirst.addEventListener('click', () => {
            this.goToFrame(0);
        });
        
        this.elements.btnLast.addEventListener('click', () => {
            this.goToFrame(this.frames.length - 1);
        });
        
        // Slider
        this.elements.slider.addEventListener('input', (e) => {
            const index = parseInt(e.target.value);
            this.goToFrame(index);
        });
        
        // Selector de índice
        this.elements.indexButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const indice = e.currentTarget.dataset.index;
                this.changeIndice(indice);
            });
        });
        
        // Botones de descarga
        this.elements.btnDownloadNdvi.addEventListener('click', () => {
            this.downloadVideo('ndvi');
        });
        
        this.elements.btnDownloadNdmi.addEventListener('click', () => {
            this.downloadVideo('ndmi');
        });
        
        this.elements.btnDownloadSavi.addEventListener('click', () => {
            this.downloadVideo('savi');
        });
        
        // Click en canvas para pausar/reanudar
        this.canvas.addEventListener('click', () => {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        });
        
        // Teclado
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case ' ':
                case 'Enter':
                    e.preventDefault();
                    if (this.isPlaying) this.pause();
                    else this.play();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.prev();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.next();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToFrame(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToFrame(this.frames.length - 1);
                    break;
            }
        });
    }
    
    /**
     * Carga datos del timeline desde la API
     */
    async loadTimelineData() {
        this.showLoading(true);
        
        try {
            console.log('📡 Cargando datos del timeline...');
            const response = await fetch(this.config.apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.mensaje || 'Error desconocido');
            }
            
            this.frames = data.frames || [];
            console.log(`✅ Cargados ${this.frames.length} frames`);
            
            // Configurar slider
            this.elements.slider.max = Math.max(0, this.frames.length - 1);
            this.elements.slider.value = 0;
            
            // Actualizar contador
            this.updateFrameCounter();
            
            // Pre-cargar algunas imágenes
            this.preloadImages(0, Math.min(3, this.frames.length));
            
        } catch (error) {
            console.error('❌ Error cargando timeline:', error);
            this.showError('Error cargando datos del timeline: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * Renderiza un frame específico
     */
    async renderFrame(index) {
        if (index < 0 || index >= this.frames.length) {
            console.warn('⚠️ Índice de frame fuera de rango:', index);
            return;
        }
        
        const previousFrame = this.frames[this.currentIndex];
        this.currentIndex = index;
        const frame = this.frames[index];
        
        // Iniciar transición si cambiamos de frame
        if (previousFrame && previousFrame !== frame) {
            this.startTransition(previousFrame, frame);
        }
        
        // Actualizar slider sin disparar evento
        this.elements.slider.value = index;
        
        // Actualizar contador
        this.updateFrameCounter();
        
        // Actualizar metadata
        this.updateMetadata(frame);
        
        // Obtener URL de imagen según índice actual
        const imageUrl = frame.imagenes[this.currentIndice];
        
        if (imageUrl) {
            // Cargar y renderizar imagen
            const img = await this.loadImage(imageUrl);
            if (img) {
                this.drawImage(img, frame);
            } else {
                this.drawPlaceholder(frame, 'Imagen no disponible');
            }
        } else {
            // Mostrar placeholder con opción de descarga
            this.drawPlaceholder(frame, 'Imagen no descargada aún');
        }
        
        // Pre-cargar imágenes adyacentes
        this.preloadImages(index - 1, index + 2);
    }
    
    /**
     * Dibuja una imagen en el canvas
     */
    drawImage(img, frame) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasWidth = rect.width;
        const canvasHeight = rect.height;
        
        // Limpiar canvas
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        
        // Calcular dimensiones para centrar y ajustar la imagen
        const imgRatio = img.width / img.height;
        const canvasRatio = canvasWidth / canvasHeight;
        
        let drawWidth, drawHeight, offsetX, offsetY;
        
        if (imgRatio > canvasRatio) {
            // Imagen más ancha
            drawWidth = canvasWidth;
            drawHeight = canvasWidth / imgRatio;
            offsetX = 0;
            offsetY = (canvasHeight - drawHeight) / 2;
        } else {
            // Imagen más alta
            drawHeight = canvasHeight;
            drawWidth = canvasHeight * imgRatio;
            offsetX = (canvasWidth - drawWidth) / 2;
            offsetY = 0;
        }
        
        // Dibujar imagen
        this.ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
        
        // Overlay con información
        this.drawOverlay(frame, canvasWidth, canvasHeight);
    }
    
    /**
     * Dibuja overlay con información del frame
     */
    drawOverlay(frame, canvasWidth, canvasHeight) {
        const clasificacion = frame.clasificaciones[this.currentIndice];
        if (!clasificacion) return;
        
        // Gradiente de fondo para el overlay
        const gradient = this.ctx.createLinearGradient(0, canvasHeight - 120, 0, canvasHeight);
        gradient.addColorStop(0, 'rgba(0, 0, 0, 0)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0.85)');
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, canvasHeight - 120, canvasWidth, 120);
        
        // Texto del período
        this.ctx.fillStyle = '#fff';
        this.ctx.font = 'bold 28px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(frame.periodo_texto, 20, canvasHeight - 80);
        
        // Valor del índice
        const valorIndice = frame[this.currentIndice].promedio;
        if (valorIndice !== null) {
            this.ctx.font = 'bold 48px Arial';
            this.ctx.fillStyle = clasificacion.color;
            const texto = `${this.currentIndice.toUpperCase()}: ${valorIndice.toFixed(3)}`;
            this.ctx.fillText(texto, 20, canvasHeight - 35);
        }
        
        // Estado (etiqueta)
        this.ctx.font = 'bold 20px Arial';
        this.ctx.fillStyle = '#fff';
        this.ctx.textAlign = 'right';
        const etiquetaCompleta = `${clasificacion.icono} ${clasificacion.etiqueta}`;
        this.ctx.fillText(etiquetaCompleta, canvasWidth - 20, canvasHeight - 70);
        
        // Descripción
        this.ctx.font = '16px Arial';
        this.ctx.fillStyle = '#ddd';
        this.ctx.fillText(clasificacion.descripcion, canvasWidth - 20, canvasHeight - 45);
        
        // Nubosidad
        if (frame.imagen_metadata.nubosidad !== null) {
            this.ctx.fillStyle = '#aaa';
            this.ctx.font = '14px Arial';
            this.ctx.fillText(
                `☁️ Nubosidad: ${frame.imagen_metadata.nubosidad.toFixed(1)}%`,
                canvasWidth - 20,
                canvasHeight - 20
            );
        }
    }
    
    /**
     * Dibuja placeholder cuando no hay imagen - Visualización con colores según índice
     */
    drawPlaceholder(frame, mensaje) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasWidth = rect.width;
        const canvasHeight = rect.height;
        
        // Limpiar canvas
        this.ctx.fillStyle = '#1a1a1a';
        this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        
        // Obtener clasificación y valor del índice actual
        const clasificacion = frame.clasificaciones[this.currentIndice];
        const valorIndice = frame[this.currentIndice].promedio;
        
        if (clasificacion && valorIndice !== null) {
            // Obtener color base (con transición si está activa)
            let baseColor = clasificacion.color;
            let currentValor = valorIndice;
            
            // Si hay transición activa, interpolar
            if (this.transition.active && this.transition.fromFrame) {
                const fromClasif = this.transition.fromFrame.clasificaciones[this.currentIndice];
                const fromValor = this.transition.fromFrame[this.currentIndice].promedio;
                
                if (fromClasif && fromValor !== null) {
                    baseColor = this.interpolateColorHex(fromClasif.color, clasificacion.color, this.transition.progress);
                    currentValor = fromValor + (valorIndice - fromValor) * this.transition.progress;
                }
            }
            
            // Crear gradiente basado en el color de clasificación
            gradient.addColorStop(0, this.hexToRgba(baseColor, 0.8));
            gradient.addColorStop(0.5, this.hexToRgba(baseColor, 0.5));
            gradient.addColorStop(1, this.hexToRgba(baseColor, 0.2));
            
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
            
            // Dibujar área de parcela representativa (rectángulo con bordes redondeados)
            const parcelaWidth = canvasWidth * 0.7;
            const parcelaHeight = canvasHeight * 0.6;
            const parcelaX = (canvasWidth - parcelaWidth) / 2;
            const parcelaY = (canvasHeight - parcelaHeight) / 2;
            
            // Sombra de parcela
            this.ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
            this.ctx.shadowBlur = 20;
            this.ctx.shadowOffsetX = 0;
            this.ctx.shadowOffsetY = 10;
            
            // Parcela con color del índice
            this.ctx.fillStyle = this.hexToRgba(baseColor, 0.9);
            this.roundRect(parcelaX, parcelaY, parcelaWidth, parcelaHeight, 20);
            this.ctx.fill();
            
            // Resetear sombra
            this.ctx.shadowColor = 'transparent';
            this.ctx.shadowBlur = 0;
            
            // Borde de parcela
            this.ctx.strokeStyle = '#fff';
            this.ctx.lineWidth = 3;
            this.roundRect(parcelaX, parcelaY, parcelaWidth, parcelaHeight, 20);
            this.ctx.stroke();
            
            // Icono del estado en el centro
            this.ctx.font = '120px Arial';
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(clasificacion.icono, canvasWidth / 2, canvasHeight / 2 - 20);
            
            // Valor del índice prominente (usar valor interpolado si hay transición)
            this.ctx.font = 'bold 56px Arial';
            this.ctx.fillStyle = '#fff';
            this.ctx.fillText(
                `${this.currentIndice.toUpperCase()}: ${currentValor.toFixed(3)}`,
                canvasWidth / 2,
                canvasHeight / 2 + 80
            );
            
            // Etiqueta del estado
            this.ctx.font = 'bold 28px Arial';
            this.ctx.fillText(clasificacion.etiqueta, canvasWidth / 2, canvasHeight / 2 + 125);
            
        } else {
            // Fallback: gradiente genérico verde
            const gradient = this.ctx.createLinearGradient(0, 0, canvasWidth, canvasHeight);
            gradient.addColorStop(0, '#2e8b57');
            gradient.addColorStop(1, '#1a4d2e');
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
            
            // Icono grande
            this.ctx.font = '120px Arial';
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText('🛰️', canvasWidth / 2, canvasHeight / 2 - 40);
            
            // Mensaje
            this.ctx.font = 'bold 24px Arial';
            this.ctx.fillStyle = '#fff';
            this.ctx.fillText(mensaje, canvasWidth / 2, canvasHeight / 2 + 60);
        }
        
        // Overlay con período (siempre mostrar)
        this.drawOverlay(frame, canvasWidth, canvasHeight);
    }
    
    /**
     * Dibuja rectángulo con bordes redondeados
     */
    roundRect(x, y, width, height, radius) {
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius, y);
        this.ctx.lineTo(x + width - radius, y);
        this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.ctx.lineTo(x + width, y + height - radius);
        this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.ctx.lineTo(x + radius, y + height);
        this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.ctx.lineTo(x, y + radius);
        this.ctx.quadraticCurveTo(x, y, x + radius, y);
        this.ctx.closePath();
    }
    
    /**
     * Convierte color hex a rgba
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    /**
     * Carga una imagen (con caché)
     */
    async loadImage(url) {
        // Verificar caché
        if (this.imageCache.has(url)) {
            return this.imageCache.get(url);
        }
        
        // Evitar cargas duplicadas
        if (this.loadingImages.has(url)) {
            // Esperar a que termine la carga en curso
            return new Promise((resolve) => {
                const checkInterval = setInterval(() => {
                    if (this.imageCache.has(url)) {
                        clearInterval(checkInterval);
                        resolve(this.imageCache.get(url));
                    }
                }, 100);
            });
        }
        
        this.loadingImages.add(url);
        
        return new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            
            img.onload = () => {
                this.imageCache.set(url, img);
                this.loadingImages.delete(url);
                console.log('✅ Imagen cargada:', url);
                resolve(img);
            };
            
            img.onerror = () => {
                this.loadingImages.delete(url);
                console.error('❌ Error cargando imagen:', url);
                resolve(null);
            };
            
            img.src = url;
        });
    }
    
    /**
     * Pre-carga imágenes
     */
    preloadImages(startIndex, endIndex) {
        for (let i = Math.max(0, startIndex); i < Math.min(endIndex, this.frames.length); i++) {
            const frame = this.frames[i];
            const imageUrl = frame.imagenes[this.currentIndice];
            
            if (imageUrl && !this.imageCache.has(imageUrl)) {
                this.loadImage(imageUrl);
            }
        }
    }
    
    /**
     * Actualiza metadata en el panel
     */
    updateMetadata(frame) {
        // Período
        this.elements.valuePeriodo.textContent = frame.periodo_texto;
        
        // Índice actual
        const clasificacion = frame.clasificaciones[this.currentIndice];
        if (clasificacion) {
            this.elements.iconIndice.textContent = clasificacion.icono;
            this.elements.valueIndice.textContent = frame[this.currentIndice].promedio?.toFixed(3) || '-';
        }
        
        // Tendencia
        if (frame.comparacion && frame.comparacion[this.currentIndice]) {
            const comp = frame.comparacion[this.currentIndice];
            this.elements.iconTendencia.textContent = comp.icono;
            this.elements.valueTendencia.textContent = `${comp.porcentaje >= 0 ? '+' : ''}${comp.porcentaje.toFixed(1)}%`;
            this.elements.valueTendencia.style.color = comp.tendencia === 'mejora' ? '#28a745' : 
                                                       comp.tendencia === 'deterioro' ? '#dc3545' : '#6c757d';
        } else {
            this.elements.iconTendencia.textContent = '➡️';
            this.elements.valueTendencia.textContent = 'Primer mes';
            this.elements.valueTendencia.style.color = '#6c757d';
        }
        
        // Calidad de datos
        const calidad = frame.calidad_datos;
        if (calidad) {
            this.elements.valueCalidad.textContent = calidad.charAt(0).toUpperCase() + calidad.slice(1);
            
            // Icono y color según calidad
            if (calidad === 'excelente') {
                this.elements.iconCalidad.textContent = '⭐⭐⭐';
                this.elements.valueCalidad.style.color = '#28a745';
            } else if (calidad === 'buena') {
                this.elements.iconCalidad.textContent = '⭐⭐';
                this.elements.valueCalidad.style.color = '#17a2b8';
            } else if (calidad === 'aceptable') {
                this.elements.iconCalidad.textContent = '⭐';
                this.elements.valueCalidad.style.color = '#ffc107';
            } else {
                this.elements.iconCalidad.textContent = '⚠️';
                this.elements.valueCalidad.style.color = '#dc3545';
            }
        } else {
            this.elements.iconCalidad.textContent = '❓';
            this.elements.valueCalidad.textContent = 'Sin datos';
            this.elements.valueCalidad.style.color = '#6c757d';
        }
        
        // Resumen simple
        this.elements.resumenSimple.textContent = frame.resumen_simple;
    }
    
    /**
     * Actualiza contador de frames
     */
    updateFrameCounter() {
        this.elements.frameCounter.textContent = 
            `${this.currentIndex + 1} / ${this.frames.length}`;
    }
    
    /**
     * Reproduce el timeline
     */
    play() {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        this.elements.btnPlay.innerHTML = '<i class="fas fa-pause"></i>';
        
        this.playInterval = setInterval(() => {
            if (this.currentIndex >= this.frames.length - 1) {
                // Fin del timeline, reiniciar
                this.goToFrame(0);
            } else {
                this.next();
            }
        }, this.playSpeed);
    }
    
    /**
     * Pausa la reproducción
     */
    pause() {
        if (!this.isPlaying) return;
        
        this.isPlaying = false;
        this.elements.btnPlay.innerHTML = '<i class="fas fa-play"></i>';
        
        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
    }
    
    /**
     * Frame siguiente
     */
    next() {
        const nextIndex = Math.min(this.currentIndex + 1, this.frames.length - 1);
        this.goToFrame(nextIndex);
    }
    
    /**
     * Frame anterior
     */
    prev() {
        const prevIndex = Math.max(this.currentIndex - 1, 0);
        this.goToFrame(prevIndex);
    }
    
    /**
     * Ir a un frame específico
     */
    async goToFrame(index) {
        if (index === this.currentIndex) return;
        await this.renderFrame(index);
    }
    
    /**
     * Cambia el índice visualizado (NDVI, NDMI, SAVI)
     */
    changeIndice(indice) {
        if (this.currentIndice === indice) return;
        
        this.currentIndice = indice;
        
        // Actualizar botones
        this.elements.indexButtons.forEach(btn => {
            if (btn.dataset.index === indice) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Re-renderizar frame actual con nuevo índice
        this.renderFrame(this.currentIndex);
    }
    
    /**
     * Muestra/oculta loading overlay
     */
    showLoading(show) {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    /**
     * Muestra error en el canvas
     */
    showError(mensaje) {
        const rect = this.canvas.getBoundingClientRect();
        const canvasWidth = rect.width;
        const canvasHeight = rect.height;
        
        this.ctx.fillStyle = '#1a1a1a';
        this.ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        
        this.ctx.font = 'bold 24px Arial';
        this.ctx.fillStyle = '#dc3545';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('❌ ' + mensaje, canvasWidth / 2, canvasHeight / 2);
    }
    
    /**
     * Inicia una transición suave entre frames
     */
    startTransition(fromFrame, toFrame) {
        // Cancelar transición anterior si existe
        if (this.transition.animationId) {
            cancelAnimationFrame(this.transition.animationId);
        }
        
        this.transition = {
            active: true,
            progress: 0,
            fromFrame: fromFrame,
            toFrame: toFrame,
            startTime: performance.now(),
            duration: 1200,
            animationId: null
        };
        
        this.animateTransition();
    }
    
    /**
     * Anima la transición
     */
    animateTransition() {
        if (!this.transition.active) return;
        
        const elapsed = performance.now() - this.transition.startTime;
        const rawProgress = Math.min(elapsed / this.transition.duration, 1);
        
        // Ease-in-out cúbico (más suave)
        const eased = rawProgress < 0.5
            ? 4 * rawProgress * rawProgress * rawProgress
            : 1 - Math.pow(-2 * rawProgress + 2, 3) / 2;
        
        this.transition.progress = eased;
        
        // Redibujar con progreso actual
        const frame = this.frames[this.currentIndex];
        const imageUrl = frame.imagenes[this.currentIndice];
        
        if (imageUrl) {
            this.loadImage(imageUrl).then(img => {
                if (img) {
                    this.drawImage(img, frame);
                } else {
                    this.drawPlaceholder(frame, 'Imagen no disponible');
                }
            });
        } else {
            this.drawPlaceholder(frame, 'Imagen no descargada aún');
        }
        
        // Continuar animación
        if (rawProgress < 1) {
            this.transition.animationId = requestAnimationFrame(() => this.animateTransition());
        } else {
            this.transition.active = false;
            this.transition.animationId = null;
        }
    }
    
    /**
     * Interpola entre dos colores hexadecimales
     */
    interpolateColorHex(hex1, hex2, progress) {
        const r1 = parseInt(hex1.slice(1, 3), 16);
        const g1 = parseInt(hex1.slice(3, 5), 16);
        const b1 = parseInt(hex1.slice(5, 7), 16);
        
        const r2 = parseInt(hex2.slice(1, 3), 16);
        const g2 = parseInt(hex2.slice(3, 5), 16);
        const b2 = parseInt(hex2.slice(5, 7), 16);
        
        const r = Math.round(r1 + (r2 - r1) * progress);
        const g = Math.round(g1 + (g2 - g1) * progress);
        const b = Math.round(b1 + (b2 - b1) * progress);
        
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
    
    /**
     * Descarga el timeline como video MP4 para un índice específico
     */
    async downloadVideo(indice) {
        // Verificar si el navegador soporta MediaRecorder
        if (!window.MediaRecorder) {
            alert('Tu navegador no soporta la grabación de video. Usa Chrome o Firefox.');
            return;
        }
        
        console.log(`🎬 Iniciando descarga de video para ${indice.toUpperCase()}...`);
        
        // Guardar estado actual
        const originalIndex = this.currentIndex;
        const originalIndice = this.currentIndice;
        const wasPlaying = this.isPlaying;
        
        // Pausar si está reproduciendo
        if (wasPlaying) {
            this.pause();
        }
        
        // Cambiar al índice solicitado
        this.changeIndice(indice);
        
        // Crear canvas temporal con mejor resolución
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = 1200;
        tempCanvas.height = 600;
        const tempCtx = tempCanvas.getContext('2d');
        
        try {
            // Capturar stream del canvas
            const stream = tempCanvas.captureStream(2); // 2 FPS
            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'video/webm;codecs=vp9',
                videoBitsPerSecond: 2500000 // 2.5 Mbps para buena calidad
            });
            
            const chunks = [];
            
            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunks.push(e.data);
                }
            };
            
            mediaRecorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `timeline_${this.config.parcelaNombre}_${indice.toUpperCase()}_${new Date().toISOString().split('T')[0]}.webm`;
                a.click();
                URL.revokeObjectURL(url);
                
                console.log('✅ Video descargado exitosamente');
                
                // Restaurar estado original
                this.changeIndice(originalIndice);
                this.goToFrame(originalIndex);
                if (wasPlaying) {
                    this.play();
                }
            };
            
            // Iniciar grabación
            mediaRecorder.start();
            console.log('🔴 Grabación iniciada');
            
            // Renderizar todos los frames
            for (let i = 0; i < this.frames.length; i++) {
                const frame = this.frames[i];
                
                // Renderizar en canvas temporal
                await this.renderFrameToCanvas(tempCanvas, tempCtx, frame, indice);
                
                // Esperar 500ms por frame (2 FPS)
                await new Promise(resolve => setTimeout(resolve, 500));
                
                console.log(`📹 Frame ${i + 1}/${this.frames.length} capturado`);
            }
            
            // Detener grabación
            mediaRecorder.stop();
            console.log('⏹️ Grabación detenida');
            
        } catch (error) {
            console.error('❌ Error al generar video:', error);
            alert('Error al generar el video. Por favor, intenta de nuevo.');
            
            // Restaurar estado original
            this.changeIndice(originalIndice);
            this.goToFrame(originalIndex);
            if (wasPlaying) {
                this.play();
            }
        }
    }
    
    /**
     * Renderiza un frame en un canvas específico con diseño profesional completo
     */
    async renderFrameToCanvas(canvas, ctx, frame, indice) {
        const canvasWidth = canvas.width;
        const canvasHeight = canvas.height;
        
        // Obtener clasificación y valor del índice
        const clasificacion = frame.clasificaciones[indice];
        const valorIndice = frame[indice].promedio;
        
        if (!clasificacion || valorIndice === null) return;
        
        const baseColor = clasificacion.color;
        
        // ========== INTENTAR CARGAR IMAGEN SATELITAL REAL ==========
        const imageUrl = frame.imagenes[indice];
        let hasRealImage = false;
        let satelliteImage = null;
        
        if (imageUrl) {
            try {
                satelliteImage = await this.loadImagePromise(imageUrl);
                hasRealImage = true;
                console.log('✅ Imagen satelital cargada para', frame.periodo_texto);
            } catch (error) {
                console.log('⚠️ No se pudo cargar imagen satelital para', frame.periodo_texto);
                hasRealImage = false;
            }
        }
        
        // ========== FONDO CON GRADIENTE ==========
        const bgGradient = ctx.createLinearGradient(0, 0, 0, canvasHeight);
        bgGradient.addColorStop(0, '#1a1a1a');
        bgGradient.addColorStop(1, '#2d2d2d');
        ctx.fillStyle = bgGradient;
        ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        
        // ========== HEADER CON INFORMACIÓN DE LA PARCELA ==========
        ctx.fillStyle = 'rgba(46, 139, 87, 0.9)';
        ctx.fillRect(0, 0, canvasWidth, 80);
        
        // Logo/Título
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 28px Arial';
        ctx.textAlign = 'left';
        ctx.fillText('🌾 AgroTech Histórico', 30, 35);
        
        // Nombre de la parcela
        ctx.font = '20px Arial';
        ctx.fillText(`Parcela: ${this.config.parcelaNombre}`, 30, 62);
        
        // Fecha en la esquina derecha
        ctx.textAlign = 'right';
        ctx.font = 'bold 24px Arial';
        ctx.fillText(frame.periodo_texto, canvasWidth - 30, 50);
        
        // ========== ÁREA PRINCIPAL ==========
        const mainAreaY = 100;
        const mainAreaHeight = 340;
        
        if (hasRealImage && satelliteImage) {
            // ===== MOSTRAR IMAGEN SATELITAL REAL =====
            const imgRatio = satelliteImage.width / satelliteImage.height;
            const areaRatio = (canvasWidth - 100) / mainAreaHeight;
            
            let drawWidth, drawHeight, offsetX, offsetY;
            
            if (imgRatio > areaRatio) {
                drawWidth = canvasWidth - 100;
                drawHeight = drawWidth / imgRatio;
                offsetX = 50;
                offsetY = mainAreaY + (mainAreaHeight - drawHeight) / 2;
            } else {
                drawHeight = mainAreaHeight;
                drawWidth = drawHeight * imgRatio;
                offsetX = 50 + (canvasWidth - 100 - drawWidth) / 2;
                offsetY = mainAreaY;
            }
            
            // Dibujar imagen satelital
            ctx.drawImage(satelliteImage, offsetX, offsetY, drawWidth, drawHeight);
            
            // Badge pequeño con estado en esquina superior derecha
            const badgeX = canvasWidth - 80;
            const badgeY = mainAreaY + 15;
            const badgeWidth = 160;
            const badgeHeight = 60;
            
            // Fondo semitransparente del badge
            ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
            ctx.beginPath();
            ctx.roundRect(badgeX - badgeWidth / 2, badgeY, badgeWidth, badgeHeight, 8);
            ctx.fill();
            
            // Borde del badge con color del índice
            ctx.strokeStyle = baseColor;
            ctx.lineWidth = 3;
            ctx.stroke();
            
            // Texto del badge
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(indice.toUpperCase(), badgeX, badgeY + 20);
            
            ctx.font = 'bold 20px Arial';
            ctx.fillStyle = baseColor;
            ctx.fillText(valorIndice.toFixed(3), badgeX, badgeY + 42);
            
            // Icono pequeño
            ctx.font = '16px Arial';
            ctx.fillStyle = '#ffffff';
            ctx.fillText(`${clasificacion.icono} ${clasificacion.etiqueta}`, badgeX, badgeY + 58);
            
            // Borde con el color del índice
            ctx.strokeStyle = baseColor;
            ctx.lineWidth = 6;
            ctx.strokeRect(50, mainAreaY, canvasWidth - 100, mainAreaHeight);
            
        } else {
            // ===== VISUALIZACIÓN CON COLORES (FALLBACK) =====
            const r = parseInt(baseColor.slice(1, 3), 16);
            const g = parseInt(baseColor.slice(3, 5), 16);
            const b = parseInt(baseColor.slice(5, 7), 16);
            
            const mainGradient = ctx.createRadialGradient(
                canvasWidth / 2, mainAreaY + mainAreaHeight / 2, 0,
                canvasWidth / 2, mainAreaY + mainAreaHeight / 2, 350
            );
            mainGradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.9)`);
            mainGradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0.3)`);
            
            ctx.fillStyle = mainGradient;
            ctx.fillRect(50, mainAreaY, canvasWidth - 100, mainAreaHeight);
            
            // Badge pequeño con estado en esquina superior derecha
            const badgeX = canvasWidth - 80;
            const badgeY = mainAreaY + 15;
            const badgeWidth = 160;
            const badgeHeight = 60;
            
            // Fondo semitransparente del badge
            ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
            ctx.beginPath();
            ctx.roundRect(badgeX - badgeWidth / 2, badgeY, badgeWidth, badgeHeight, 8);
            ctx.fill();
            
            // Borde del badge con color del índice
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 3;
            ctx.stroke();
            
            // Texto del badge
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(indice.toUpperCase(), badgeX, badgeY + 20);
            
            ctx.font = 'bold 20px Arial';
            ctx.fillStyle = '#ffffff';
            ctx.fillText(valorIndice.toFixed(3), badgeX, badgeY + 42);
            
            // Icono pequeño
            ctx.font = '16px Arial';
            ctx.fillStyle = '#ffffff';
            ctx.fillText(`${clasificacion.icono} ${clasificacion.etiqueta}`, badgeX, badgeY + 58);
            
            // Borde con el color del índice
            ctx.strokeStyle = baseColor;
            ctx.lineWidth = 6;
            ctx.strokeRect(50, mainAreaY, canvasWidth - 100, mainAreaHeight);
        }
        
        // ========== PANEL INFERIOR CON DATOS ADICIONALES ==========
        const bottomY = 460;
        
        // Fondo del panel de datos
        ctx.fillStyle = 'rgba(30, 30, 30, 0.95)';
        ctx.fillRect(0, bottomY, canvasWidth, 140);
        
        // Línea separadora superior
        ctx.strokeStyle = baseColor;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(0, bottomY);
        ctx.lineTo(canvasWidth, bottomY);
        ctx.stroke();
        
        // ========== GRID DE INFORMACIÓN (4 columnas) ==========
        ctx.textAlign = 'center';
        const colWidth = canvasWidth / 4;
        
        // COLUMNA 1: Índice Principal
        let col1X = colWidth / 2;
        ctx.fillStyle = '#888';
        ctx.font = '16px Arial';
        ctx.fillText(`ÍNDICE ${indice.toUpperCase()}`, col1X, bottomY + 30);
        
        // Valor e ícono del índice principal
        ctx.font = '28px Arial';
        ctx.fillStyle = '#ffffff';
        ctx.fillText(clasificacion.icono, col1X, bottomY + 60);
        
        ctx.font = 'bold 32px Arial';
        ctx.fillStyle = baseColor;
        ctx.fillText(valorIndice.toFixed(3), col1X, bottomY + 95);
        
        ctx.font = 'bold 18px Arial';
        ctx.fillStyle = '#aaa';
        ctx.fillText(clasificacion.etiqueta, col1X, bottomY + 118);
        
        // COLUMNA 2: Cambio vs Anterior
        let col2X = colWidth * 1.5;
        ctx.fillStyle = '#888';
        ctx.font = '16px Arial';
        ctx.fillText('CAMBIO VS ANTERIOR', col2X, bottomY + 30);
        
        if (frame.comparacion && frame.comparacion[indice]) {
            const comp = frame.comparacion[indice];
            ctx.font = 'bold 32px Arial';
            ctx.fillStyle = comp.tendencia === 'mejora' ? '#28a745' : 
                           comp.tendencia === 'deterioro' ? '#dc3545' : '#ffc107';
            ctx.fillText(
                `${comp.icono} ${comp.porcentaje >= 0 ? '+' : ''}${comp.porcentaje.toFixed(1)}%`,
                col2X,
                bottomY + 70
            );
            ctx.font = 'bold 18px Arial';
            ctx.fillStyle = '#aaa';
            ctx.fillText(comp.tendencia === 'mejora' ? 'Mejora' : 
                        comp.tendencia === 'deterioro' ? 'Deterioro' : 'Estable',
                col2X, bottomY + 95);
        } else {
            ctx.font = 'bold 24px Arial';
            ctx.fillStyle = '#888';
            ctx.fillText('Primer mes', col2X, bottomY + 70);
        }
        
        // COLUMNA 3: Índices adicionales
        let col3X = colWidth * 2.5;
        ctx.fillStyle = '#888';
        ctx.font = '16px Arial';
        ctx.fillText('OTROS ÍNDICES', col3X, bottomY + 30);
        
        // Mostrar los otros 2 índices
        const otrosIndices = ['ndvi', 'ndmi', 'savi'].filter(i => i !== indice);
        ctx.font = 'bold 20px Arial';
        ctx.fillStyle = '#17a2b8';
        ctx.textAlign = 'center';
        ctx.fillText(
            `${otrosIndices[0].toUpperCase()}: ${(frame[otrosIndices[0]].promedio || 0).toFixed(3)}`,
            col3X, bottomY + 60
        );
        ctx.fillText(
            `${otrosIndices[1].toUpperCase()}: ${(frame[otrosIndices[1]].promedio || 0).toFixed(3)}`,
            col3X, bottomY + 88
        );
        
        // COLUMNA 4: Clima y Calidad
        let col4X = colWidth * 3.5;
        ctx.fillStyle = '#888';
        ctx.font = '16px Arial';
        ctx.fillText('CLIMA & CALIDAD', col4X, bottomY + 30);
        
        // Datos climáticos
        ctx.font = 'bold 20px Arial';
        ctx.fillStyle = '#ff9800';
        if (frame.temperatura !== null) {
            ctx.fillText(`🌡️ ${frame.temperatura.toFixed(1)}°C`, col4X, bottomY + 58);
        }
        ctx.fillStyle = '#2196f3';
        if (frame.precipitacion !== null) {
            ctx.fillText(`💧 ${frame.precipitacion.toFixed(1)}mm`, col4X, bottomY + 82);
        }
        
        // Calidad de imagen
        const calidad = frame.calidad_datos;
        if (calidad) {
            let calidadIcono = '';
            let calidadColor = '';
            
            if (calidad === 'excelente') {
                calidadIcono = '⭐⭐⭐';
                calidadColor = '#28a745';
            } else if (calidad === 'buena') {
                calidadIcono = '⭐⭐';
                calidadColor = '#17a2b8';
            } else if (calidad === 'aceptable') {
                calidadIcono = '⭐';
                calidadColor = '#ffc107';
            } else {
                calidadIcono = '⚠️';
                calidadColor = '#dc3545';
            }
            
            ctx.font = '20px Arial';
            ctx.fillStyle = calidadColor;
            ctx.fillText(calidadIcono, col4X, bottomY + 106);
            
            ctx.font = 'bold 16px Arial';
            ctx.fillText(calidad.charAt(0).toUpperCase() + calidad.slice(1), col4X, bottomY + 125);
        }
        
        // ========== PIE DE PÁGINA ==========
        ctx.fillStyle = 'rgba(46, 139, 87, 0.8)';
        ctx.fillRect(0, 600, canvasWidth, 0);
        
        // Marca de agua
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.font = '14px Arial';
        ctx.textAlign = 'left';
        const now = new Date();
        ctx.fillText(
            `Generado: ${now.toLocaleDateString('es-ES')} ${now.toLocaleTimeString('es-ES')}`,
            30, 
            bottomY + 125
        );
        
        ctx.textAlign = 'right';
        ctx.fillText('AgroTech Histórico © 2025', canvasWidth - 30, bottomY + 125);
    }
    
    /**
     * Carga una imagen como Promise
     */
    loadImagePromise(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => resolve(img);
            img.onerror = () => reject(new Error('No se pudo cargar la imagen'));
            img.src = url;
        });
    }
}

// Exportar para uso global
window.TimelinePlayer = TimelinePlayer;

