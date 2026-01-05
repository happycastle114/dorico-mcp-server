# Dorico MCP Server - Feature Specification

## 🎯 Target User Profile

**작곡 전공자 (Composition Major)**
- 화성학 (Harmony) 지식 보유
- 오케스트레이션 (Orchestration) 학습 중
- 대위법 (Counterpoint) 연습 필요
- 악보 교정 (Proofreading) 빈번

---

## 📋 Feature Categories

### 1. Core Score Tools (악보 기본 도구)

| Tool | Description | Priority | Dorico API |
|------|-------------|----------|------------|
| `create_score` | 새 악보 생성 (악기 구성 포함) | HIGH | `File.New`, `Edit.AddInstruments` |
| `open_score` | 기존 악보 열기 | HIGH | `File.Open` |
| `save_score` | 악보 저장 | HIGH | `File.Save` |
| `export_score` | PDF/MusicXML 내보내기 | MEDIUM | `File.Export*` |

### 2. Note Input Tools (음표 입력 도구)

| Tool | Description | Priority | Dorico API |
|------|-------------|----------|------------|
| `add_notes` | 음표 추가 (피치, 리듬, 옥타브) | HIGH | `NoteInput.*` |
| `add_rest` | 쉼표 추가 | HIGH | `NoteInput.Rest` |
| `add_chord` | 화음 추가 | HIGH | Multiple `NoteInput` |
| `delete_notes` | 선택된 음표 삭제 | MEDIUM | `Edit.Delete` |
| `transpose` | 음표 전조 | MEDIUM | `Edit.Transpose*` |

### 3. Notation Tools (기보법 도구)

| Tool | Description | Priority | Dorico API |
|------|-------------|----------|------------|
| `set_key_signature` | 조표 설정 | HIGH | `Edit.AddKeySignature` |
| `set_time_signature` | 박자표 설정 | HIGH | `Edit.AddTimeSignature` |
| `add_dynamics` | 다이나믹 추가 (p, f, mf 등) | HIGH | `Edit.AddDynamics` |
| `add_articulation` | 아티큘레이션 추가 | HIGH | `Edit.AddArticulation` |
| `add_slur` | 슬러 추가 | MEDIUM | `Edit.AddSlur` |
| `add_tempo` | 템포 마킹 추가 | MEDIUM | `Edit.AddTempo` |
| `add_text` | 텍스트/지시어 추가 | MEDIUM | `Edit.AddText` |

### 4. Harmony Tools (화성학 도구) ⭐ 핵심

| Tool | Description | Priority | Implementation |
|------|-------------|----------|----------------|
| `analyze_chord` | 코드 분석 (로마 숫자 표기) | HIGH | music21 integration |
| `suggest_next_chord` | 다음 코드 제안 | HIGH | AI + music theory rules |
| `generate_progression` | 코드 진행 생성 | HIGH | Preset progressions + AI |
| `realize_figured_bass` | 계명창(숫자저음) 실현 | HIGH | music21 integration |
| `check_voice_leading` | 성부 진행 검사 | HIGH | Rule-based analysis |
| `detect_parallel_motion` | 병행 5도/8도 감지 | HIGH | Interval analysis |
| `suggest_cadence` | Cadence suggestions | HIGH | Theory-based suggestions |

### 5. Orchestration Tools (오케스트레이션 도구)

| Tool | Description | Priority | Implementation |
|------|-------------|----------|----------------|
| `add_instrument` | 악기 추가 | HIGH | Dorico API |
| `remove_instrument` | 악기 제거 | MEDIUM | Dorico API |
| `check_range` | 악기 음역 검사 | HIGH | Built-in range database |
| `suggest_doubling` | Doubling suggestions | HIGH | Orchestration rules |
| `transpose_for_instrument` | 이조 악기 처리 | HIGH | Transposition table |
| `suggest_instrumentation` | Instrumentation suggestions | HIGH | AI + orchestration guides |
| `balance_dynamics` | 밸런스 조정 제안 | LOW | Orchestration rules |

### 6. Counterpoint Tools (대위법 도구)

| Tool | Description | Priority | Implementation |
|------|-------------|----------|----------------|
| `check_species_rules` | 종별 대위법 규칙 검사 | HIGH | Rule-based |
| `generate_counterpoint` | 대위 선율 생성 | MEDIUM | AI + Fux rules |
| `analyze_intervals` | 음정 분석 | HIGH | Interval calculation |
| `find_dissonances` | Find dissonances | HIGH | Consonance/dissonance rules |

### 7. Proofreading Tools (교정 도구)

| Tool | Description | Priority | Implementation |
|------|-------------|----------|----------------|
| `check_playability` | 연주 가능성 검사 | HIGH | Technique rules |
| `check_enharmonic` | 이명동음 검사 | MEDIUM | Context analysis |
| `check_beaming` | 빔 규칙 검사 | LOW | Notation rules |
| `check_spacing` | 음표 간격 검사 | LOW | Layout analysis |
| `validate_score` | 전체 악보 검증 | HIGH | Aggregate checks |

---

## 🔧 MCP Resources

| URI | Description | Returns |
|-----|-------------|---------|
| `dorico://status` | Dorico 연결 상태 | Connection status |
| `dorico://score/info` | 현재 악보 정보 | Title, composer, instruments |
| `dorico://score/selection` | 현재 선택 정보 | Selected notes, bars |
| `dorico://instruments/list` | 사용 가능한 악기 목록 | Instrument names, ranges |
| `dorico://instruments/ranges` | 악기 음역 데이터베이스 | Pitch ranges per instrument |

---

## 💡 MCP Prompts (워크플로우)

### 1. `harmonize_melody`
**Purpose**: 멜로디에 화성 붙이기
**Steps**:
1. 멜로디 분석 (조성, 리듬)
2. 화음 제안 (코드 진행)
3. 베이스 라인 생성
4. 중간 성부 채우기
5. 성부 진행 검사

### 2. `orchestrate_piano_score`
**Purpose**: 피아노 악보를 관현악 편곡
**Steps**:
1. 피아노 악보 분석
2. 악기 편성 제안
3. 레지스터 분배
4. 더블링 제안
5. 밸런스 조정

### 3. `species_counterpoint_exercise`
**Purpose**: 종별 대위법 연습
**Steps**:
1. Cantus Firmus 입력
2. 종별 선택 (1-5종)
3. 대위 선율 생성/제안
4. 규칙 검사
5. 수정 제안

### 4. `chord_progression_workshop`
**Purpose**: 코드 진행 실습
**Steps**:
1. 조성 및 형식 설정
2. 기본 진행 생성
3. 대리 화음 제안
4. 변형 옵션 제시
5. 악보에 적용

### 5. `score_review`
**Purpose**: 악보 전체 검토
**Steps**:
1. 음역 검사
2. 성부 진행 검사
3. 연주 가능성 검사
4. 기보법 검사
5. 종합 리포트

---

## 🎹 Instrument Range Database

```python
INSTRUMENT_RANGES = {
    # Woodwinds
    "piccolo": ("D5", "C8"),
    "flute": ("C4", "D7"),
    "oboe": ("Bb3", "G6"),
    "clarinet_bb": ("D3", "Bb6"),  # Written pitch
    "bassoon": ("Bb1", "Eb5"),
    
    # Brass
    "horn_f": ("F#2", "C6"),  # Written pitch
    "trumpet_bb": ("F#3", "D6"),  # Written pitch
    "trombone": ("E2", "Bb4"),
    "tuba": ("D1", "F4"),
    
    # Strings
    "violin": ("G3", "E7"),
    "viola": ("C3", "E6"),
    "cello": ("C2", "A5"),
    "double_bass": ("E1", "G4"),  # Written octave higher
    
    # Percussion
    "timpani": ("D2", "C4"),
    "xylophone": ("F4", "C8"),
    "marimba": ("C2", "C7"),
    
    # Keyboard
    "piano": ("A0", "C8"),
    "harp": ("Cb1", "G#7"),
}
```

---

## 📊 Priority Matrix

| Category | Must Have | Should Have | Nice to Have |
|----------|-----------|-------------|--------------|
| **Core** | create, save, notes | export, delete | undo/redo |
| **Notation** | key, time, dynamics | articulation, slur | text, lines |
| **Harmony** | analyze, suggest, progression | figured bass, check | cadence |
| **Orchestration** | add instrument, range | doubling, transpose | balance |
| **Counterpoint** | rules check | generate | species-specific |
| **Proofreading** | playability, validate | enharmonic | beaming |

---

## 🔄 Implementation Phases

### Phase 1: Foundation (Week 1) ✅
- [x] Dorico WebSocket client
- [x] Basic MCP server setup
- [x] Core score tools (create, save, open)
- [x] Note input tools

### Phase 2: Notation (Week 2) ✅
- [x] Key/time signature tools
- [x] Dynamics and articulation
- [x] Slurs and ties
- [x] Basic resources

### Phase 3: Harmony (Week 3) ✅
- [x] music21 integration
- [x] Chord analysis
- [x] Progression generation
- [x] Voice leading check

### Phase 4: Advanced (Week 4) ✅
- [x] Orchestration tools
- [x] Counterpoint tools (check_species_rules, generate_counterpoint)
- [x] Proofreading tools (range check, validate_voice_leading, check_enharmonic)
- [x] Workflow prompts

### Phase 5: Polish (Week 5) ✅
- [x] Error handling refinement
- [x] Performance optimization (LRU cache for instruments, response caching)
- [x] Documentation (README examples, tool reference table)
- [x] All MEDIUM priority tools (suggest_cadence, suggest_doubling, find_dissonances, suggest_instrumentation)
- [x] All LOW priority tools (balance_dynamics, check_beaming, check_spacing)
- [x] Missing HIGH priority tools (open_score, add_articulation)
- [x] Additional tools (add_text, delete_notes, remove_instrument, add_slur)
- [x] All 5 MCP Resources implemented
- [x] All 5 MCP Prompts implemented
- [ ] User testing (requires Dorico installation)

### Final Statistics
- **51 MCP Tools** (all HIGH, MEDIUM, LOW priority)
- **5 MCP Resources** (status, score/info, score/selection, instruments/list, instruments/ranges)
- **5 MCP Prompts** (harmonize_melody, orchestration_basics, species_counterpoint, chord_progression_workshop, score_review)
- **200 Tests** passing
- **67% Coverage**
