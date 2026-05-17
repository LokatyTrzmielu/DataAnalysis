<template>
  <div ref="containerRef" class="bin3d-container">
    <div v-if="!variant" class="bin3d-empty">
      Pick a variant on the left to see the 3D preview.
    </div>
    <div class="bin3d-caption" v-if="variant">
      <span class="caption-primary">{{ variant.code }}</span>
      <span class="caption-secondary">
        — {{ variant.locations_per_bin }} cells, {{ variant.cell_length_mm }}×{{ variant.cell_width_mm }}×{{ variant.cell_height_mm }} mm
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as THREE from 'three'
import type { VariantInfo } from '@/api/containerOrder'

const props = defineProps<{ variant: VariantInfo | null }>()

const containerRef = ref<HTMLDivElement | null>(null)

let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let binGroup: THREE.Group | null = null
let frameId = 0
let isDragging = false
let lastPointer = { x: 0, y: 0 }
let rotation = { x: -0.45, y: 0.55 }

// Bin externally is 640×440 mm. Render in scene units of 1 unit = 100 mm.
const EXT_L = 6.4
const EXT_W = 4.4
const INT_L = 6.17
const INT_W = 4.08
const WALL = 0.06

const BIN_COLOR = 0x3a6fa5 // Silver Fir Blue from Kardex flyer
const DIVIDER_COLOR = 0x6b95c7
const FLOOR_COLOR = 0x2e587f

function setup(el: HTMLDivElement) {
  scene = new THREE.Scene()
  scene.background = new THREE.Color(currentSceneBg())

  const width = el.clientWidth || 400
  const height = el.clientHeight || 320
  camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100)
  camera.position.set(8, 7, 9)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.setSize(width, height)
  el.appendChild(renderer.domElement)

  scene.add(new THREE.AmbientLight(0xffffff, 0.7))
  const key = new THREE.DirectionalLight(0xffffff, 0.85)
  key.position.set(6, 10, 5)
  scene.add(key)
  const fill = new THREE.DirectionalLight(0xffffff, 0.3)
  fill.position.set(-6, 4, -3)
  scene.add(fill)

  binGroup = new THREE.Group()
  scene.add(binGroup)

  renderer.domElement.addEventListener('pointerdown', onPointerDown)
  renderer.domElement.addEventListener('pointermove', onPointerMove)
  renderer.domElement.addEventListener('pointerup', onPointerUp)
  renderer.domElement.addEventListener('pointerleave', onPointerUp)
  renderer.domElement.style.cursor = 'grab'

  animate()
}

function clearBin() {
  if (!binGroup) return
  while (binGroup.children.length) {
    const c = binGroup.children[0]
    if (!c) break
    binGroup.remove(c)
    const mesh = c as THREE.Mesh
    if (mesh.geometry) mesh.geometry.dispose()
  }
}

function buildBin(v: VariantInfo) {
  if (!binGroup) return
  clearBin()

  const heightUnits = v.bin_height_mm / 100
  const cellL = v.cell_length_mm / 100
  const cellW = v.cell_width_mm / 100
  const cellH = (v.cell_height_mm) / 100

  const material = new THREE.MeshStandardMaterial({
    color: BIN_COLOR, metalness: 0.1, roughness: 0.55, transparent: true, opacity: 0.92,
  })
  const dividerMat = new THREE.MeshStandardMaterial({
    color: DIVIDER_COLOR, metalness: 0.1, roughness: 0.6, transparent: true, opacity: 0.88,
  })
  const floorMat = new THREE.MeshStandardMaterial({
    color: FLOOR_COLOR, metalness: 0.1, roughness: 0.5,
  })

  // Floor (slightly below cell bottom)
  const floor = new THREE.Mesh(new THREE.BoxGeometry(EXT_L, 0.06, EXT_W), floorMat)
  floor.position.y = -heightUnits / 2 + 0.03
  binGroup.add(floor)

  // 4 walls
  const longWallGeo = new THREE.BoxGeometry(EXT_L, heightUnits, WALL)
  const shortWallGeo = new THREE.BoxGeometry(WALL, heightUnits, EXT_W)

  const wallFront = new THREE.Mesh(longWallGeo, material)
  wallFront.position.set(0, 0, EXT_W / 2 - WALL / 2)
  binGroup.add(wallFront)
  const wallBack = new THREE.Mesh(longWallGeo, material)
  wallBack.position.set(0, 0, -EXT_W / 2 + WALL / 2)
  binGroup.add(wallBack)
  const wallLeft = new THREE.Mesh(shortWallGeo, material)
  wallLeft.position.set(-EXT_L / 2 + WALL / 2, 0, 0)
  binGroup.add(wallLeft)
  const wallRight = new THREE.Mesh(shortWallGeo, material)
  wallRight.position.set(EXT_L / 2 - WALL / 2, 0, 0)
  binGroup.add(wallRight)

  // Dividers inside the usable area: figure out how many along each axis.
  const colsAlongL = Math.max(1, Math.round(INT_L / cellL))
  const rowsAlongW = Math.max(1, Math.round(INT_W / cellW))

  // Vertical dividers (perpendicular to length axis).
  const dividerHeight = Math.min(heightUnits - 0.1, cellH + 0.06)
  for (let i = 1; i < colsAlongL; i++) {
    const x = -INT_L / 2 + i * cellL
    const div = new THREE.Mesh(
      new THREE.BoxGeometry(0.04, dividerHeight, INT_W),
      dividerMat,
    )
    div.position.set(x, -heightUnits / 2 + dividerHeight / 2 + 0.06, 0)
    binGroup.add(div)
  }
  for (let j = 1; j < rowsAlongW; j++) {
    const z = -INT_W / 2 + j * cellW
    const div = new THREE.Mesh(
      new THREE.BoxGeometry(INT_L, dividerHeight, 0.04),
      dividerMat,
    )
    div.position.set(0, -heightUnits / 2 + dividerHeight / 2 + 0.06, z)
    binGroup.add(div)
  }

  // Centre the bin vertically so it stays in view.
  binGroup.position.y = 0
}

function animate() {
  frameId = requestAnimationFrame(animate)
  if (!scene || !camera || !renderer || !binGroup) return
  binGroup.rotation.x = rotation.x
  binGroup.rotation.y = rotation.y
  renderer.render(scene, camera)
}

function onPointerDown(e: PointerEvent) {
  isDragging = true
  lastPointer = { x: e.clientX, y: e.clientY }
  if (renderer) renderer.domElement.style.cursor = 'grabbing'
}
function onPointerMove(e: PointerEvent) {
  if (!isDragging) return
  const dx = e.clientX - lastPointer.x
  const dy = e.clientY - lastPointer.y
  rotation.y += dx * 0.01
  rotation.x = Math.max(-1.4, Math.min(1.4, rotation.x + dy * 0.01))
  lastPointer = { x: e.clientX, y: e.clientY }
}
function onPointerUp() {
  isDragging = false
  if (renderer) renderer.domElement.style.cursor = 'grab'
}

function handleResize() {
  if (!containerRef.value || !camera || !renderer) return
  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

function currentSceneBg(): number {
  return document.documentElement.classList.contains('dark') ? 0x1c1c1e : 0xf3f4f6
}

let themeObserver: MutationObserver | null = null
function watchTheme() {
  themeObserver = new MutationObserver(() => {
    if (scene) scene.background = new THREE.Color(currentSceneBg())
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
}

onMounted(() => {
  if (!containerRef.value) return
  setup(containerRef.value)
  if (props.variant) buildBin(props.variant)
  window.addEventListener('resize', handleResize)
  watchTheme()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(frameId)
  window.removeEventListener('resize', handleResize)
  if (themeObserver) themeObserver.disconnect()
  if (renderer) {
    renderer.dispose()
    renderer.domElement.remove()
  }
})

watch(() => props.variant, (v) => {
  if (v) buildBin(v)
  else clearBin()
})
</script>

<style scoped>
.bin3d-container {
  position: relative;
  width: 100%;
  height: 320px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  overflow: hidden;
}
.bin3d-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-sec);
  font-size: 13px;
  text-align: center;
  padding: 16px;
}
/* Single color for the whole chip; secondary span fades via opacity so we
   never have to worry about a per-span dark-mode override missing. */
.bin3d-caption {
  position: absolute;
  left: 12px;
  bottom: 10px;
  font-size: 11.5px;
  background: #ffffff;
  color: #1d1d1f;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid var(--app-border);
  pointer-events: none;
}
.bin3d-caption .caption-primary { font-weight: 600; }
.bin3d-caption .caption-secondary { opacity: 0.7; margin-left: 6px; }

:global(html.dark) .bin3d-caption {
  background: #1d1d1f;
  color: #f5f5f7;
  border-color: rgba(255, 255, 255, 0.22);
}
</style>
