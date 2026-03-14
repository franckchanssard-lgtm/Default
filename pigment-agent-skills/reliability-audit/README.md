# Pigment Workspace Reliability Audit

Outil d'audit automatisé pour évaluer la **fiabilité** d'un workspace Pigment.

> **Fiabilité** = Performance + Confiance dans les données + Stabilité des processus

---

## Table des matières

1. [Méthodologie](#méthodologie)
2. [Inputs requis](#inputs-requis)
3. [Les 9 Analyzers](#les-9-analyzers)
4. [KPIs détaillés](#kpis-détaillés)
5. [Scoring](#scoring)
6. [Utilisation](#utilisation)
7. [Interprétation des résultats](#interprétation-des-résultats)

---

## Méthodologie

### Philosophie

L'audit répond à **3 questions fondamentales** :

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PERFORMANCE                                                  │
│     "Le workspace est-il rapide et optimisé ?"                  │
│     → Temps d'exécution, scoping, dimensions                    │
├─────────────────────────────────────────────────────────────────┤
│  2. CONFIANCE (TRUST)                                           │
│     "Peut-on faire confiance aux données ?"                     │
│     → Fraîcheur, stabilité, cohérence                           │
├─────────────────────────────────────────────────────────────────┤
│  3. GOUVERNANCE                                                  │
│     "Le workspace est-il bien géré ?"                           │
│     → Permissions, versions, usage réel                         │
└─────────────────────────────────────────────────────────────────┘
```

### Flux de données

```
                         INPUTS
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐       ┌──────────┐       ┌──────────┐
   │   CSV   │       │ Metadata │       │  Audit   │
   │  Files  │       │   API    │       │Logs API  │
   └────┬────┘       └────┬─────┘       └────┬─────┘
        │                 │                  │
        ▼                 ▼                  ▼
   ┌─────────────────────────────────────────────┐
   │              9 ANALYZERS                     │
   │                                              │
   │  CSV-based:           API-based:            │
   │  • Performance        • Usage               │
   │  • Scoping            • Version             │
   │  • Complexity         • Permission          │
   │  • Workload                                 │
   │  • AccessRights                             │
   │  • DataQuality                              │
   └──────────────────┬──────────────────────────┘
                      │
                      ▼
   ┌─────────────────────────────────────────────┐
   │              OUTPUTS                         │
   │                                              │
   │  • Performance Score: /100 (Grade A-F)      │
   │  • Trust Score: /100 (Level HIGH-CRITICAL)  │
   │  • Recommendations priorisées               │
   │  • Rapport HTML + CSV                       │
   └─────────────────────────────────────────────┘
```

---

## Inputs requis

### Fichiers CSV

| Fichier | Obligatoire | Contenu | Utilisé par |
|---------|-------------|---------|-------------|
| `Executions.csv` | ✅ Oui | Temps d'exécution des metrics | Performance, Scoping, Complexity, DataQuality |
| `Views_Executions.csv` | ❌ Non | Temps de rendu des views/boards | Workload |
| `Armset_Upmset.csv` | ❌ Non | Exécutions ARM/UPM (sécurité) | AccessRights |

### Clés API

| API | Obligatoire | Ce qu'elle apporte |
|-----|-------------|-------------------|
| Metadata API | ❌ Non | Vrais noms (apps, blocks), dimensions, versions |
| Audit Logs API | ❌ Non | Usage réel, power users, changements, permissions |

---

## Les 9 Analyzers

### 1. PerformanceAnalyzer
**Source:** `Executions.csv`
**Question:** Les calculs sont-ils rapides ?

| KPI | Description | Seuils |
|-----|-------------|--------|
| `avg_execution_time_ms` | Temps moyen d'exécution | Watch: 3s, Warning: 5s, Critical: 30s |
| `p95_execution_time_ms` | 95ème percentile | Alerte si > 10s |
| `critical_count` | Nb de metrics > 30s | Chaque metric critique = -1 point |
| `warning_count` | Nb de metrics > 5s | Indicateur d'alerte |

---

### 2. ScopingAnalyzer
**Source:** `Executions.csv`
**Question:** Les formules sont-elles optimisées ?

| KPI | Description | Seuils |
|-----|-------------|--------|
| `fully_scoped_pct` | % de formules FullyScoped | Cible: > 50% |
| `no_change_pct` | % de formules non scopées | Critical: > 50% |
| `potential_savings_ms` | Temps économisable avec scoping | Indicateur ROI |

**Explication du scoping:**
- `FullyScoped`: Seules les cellules impactées sont recalculées ✅
- `PartiallyScoped`: Recalcul partiel ⚠️
- `NoChange`: Tout est recalculé à chaque fois ❌

---

### 3. ComplexityAnalyzer
**Source:** `Executions.csv`
**Question:** Le modèle est-il trop complexe ?

| KPI | Description | Seuils |
|-----|-------------|--------|
| `avg_dimensions` | Nb moyen de dimensions par metric | Alerte si > 5 |
| `metrics_over_10_dims` | Nb de metrics avec > 10 dimensions | Critical: chaque metric |
| `avg_computed_rows` | Nb moyen de lignes calculées | Watch: 500K, Critical: 10M |
| `dims_time_correlation` | Corrélation dimensions ↔ temps | > 0.5 = impact fort |

---

### 4. WorkloadAnalyzer
**Source:** `Views_Executions.csv`
**Question:** La charge est-elle équilibrée ?

| KPI | Description | Seuils |
|-----|-------------|--------|
| `slow_views_pct` | % de views > 3s | Alerte si > 20% |
| `top_app_pct` | % du compute par l'app la plus lourde | Alerte si > 50% |
| `avg_render_time_ms` | Temps moyen de rendu | Watch: 2s, Critical: 15s |

---

### 5. AccessRightsAnalyzer
**Source:** `Armset_Upmset.csv`
**Question:** La sécurité impacte-t-elle la performance ?

| KPI | Description | Seuils |
|-----|-------------|--------|
| `pct_time_in_security` | % du compute consommé par ARM/UPM | Alerte si > 20% |
| `slow_blocks` | Blocks ARM/UPM avec avg > 5s | Liste prioritaire |
| `frequent_recalc_blocks` | Blocks recalculés > 50 fois | Cascade détectée |
| `scoping_opportunity` | Executions ARM/UPM non scopées | Optimisation possible |

**Concepts:**
- **ARM** (Access Rights Metrics): Définit quelles données un user peut VOIR
- **UPM** (User Permission Metrics): Définit quelles actions un user peut FAIRE

---

### 6. DataQualityAnalyzer
**Source:** `Executions.csv`
**Question:** Peut-on faire confiance aux données ?

#### 6.1 Data Freshness
| KPI | Description | Seuils |
|-----|-------------|--------|
| `stale_metrics` | Metrics sans exécution depuis > 7j | Données potentiellement obsolètes |
| `very_stale_metrics` | Metrics sans exécution depuis > 30j | Données probablement obsolètes |
| `avg_data_age_days` | Age moyen des données | Indicateur global |

#### 6.2 Execution Stability
| KPI | Description | Seuils |
|-----|-------------|--------|
| `coefficient_of_variation` | Variabilité du temps d'exécution (std/mean) | > 0.5 = instable, > 1.0 = très instable |
| `execution_time_trend` | Tendance week-over-week | "improving", "stable", "degrading" |
| `highly_unstable_metrics` | Nb de metrics avec CV > 1.0 | Calculs imprévisibles |

#### 6.3 Data Flow Health
| KPI | Description | Interprétation |
|-----|-------------|----------------|
| `metrics_with_zero_rows` | Metrics qui calculent 0 lignes | Données qui ne circulent pas |
| `upsert_ratio` | Ratio upserted/computed | Haut = beaucoup de nouvelles données |
| `metrics_with_row_anomalies` | Metrics avec comptage incohérent | Problèmes de source |

#### 6.4 Scenario Coverage
| KPI | Description | Seuils |
|-----|-------------|--------|
| `total_scenarios` | Nb de scénarios | Inventaire |
| `underutilized_scenarios` | Scénarios avec < 5% des exécutions | À vérifier |
| `scenario_imbalance_ratio` | Ratio max/min exécutions | > 10 = déséquilibre |

#### 6.5 Change Velocity
| KPI | Description | Seuils |
|-----|-------------|--------|
| `changes_per_day` | Nb moyen de changements/jour | > 50 = haute vélocité |
| `change_trend` | Tendance des changements | "increasing", "stable", "decreasing" |

#### 6.6 Batch Reliability
| KPI | Description | Interprétation |
|-----|-------------|----------------|
| `batch_ratio` | % d'exécutions batch vs interactives | Indicateur d'automatisation |
| `missing_batch_days` | Jours sans batch (si pattern attendu) | Process cassé |
| `off_hours_executions_pct` | % d'exécutions hors heures | Batch nocturnes |

---

### 7. UsageAnalyzer
**Source:** Audit Logs API
**Question:** Quels sont les chemins critiques ?

| KPI | Description | Valeur |
|-----|-------------|--------|
| `top_boards` | Boards les plus consultés | Priorisation |
| `slow_popular_boards` | Boards lents mais très utilisés | Quick wins |
| `power_users` | Users avec > 100 actions | Stakeholders clés |
| `recent_imports` | Imports récents | Impact sur performance |
| `critical_paths` | Chemins à optimiser en priorité | Actions SA |

**Types de Critical Paths:**
- `high_traffic_slow`: Board lent mais très utilisé
- `import_heavy`: Application avec beaucoup d'imports
- `power_user_bottleneck`: Power user impacté par la lenteur

---

### 8. VersionAnalyzer
**Source:** Metadata API
**Question:** La dimension Version est-elle bien gérée ?

| KPI | Description | Seuils |
|-----|-------------|--------|
| `total_versions` | Nb total de versions | > 30 = attention |
| `archive_candidates` | Versions > 2 ans | À archiver |
| `high_risk_dimensions` | Dimensions avec trop de versions | Impact performance |
| `naming_issues` | Versions mal nommées | Maintenance difficile |

---

### 9. PermissionAnalyzer
**Source:** Audit Logs API
**Question:** Les droits sont-ils bien gérés ?

| KPI | Description | Seuils |
|-----|-------------|--------|
| `admin_users` | Nb d'admins | > 5 = réviser |
| `power_users` | Users avec > 100 actions | Stakeholders |
| `inactive_users` | Users sans activité > 30j | Accès à révoquer |
| `permission_changes_count` | Nb de changements de permissions | Haute fréquence = instabilité |
| `risks` | Risques identifiés | Liste priorisée |

---

## Scoring

### Performance Score (0-100)

```
Performance Score = Performance + Optimization + Complexity + Views
                         /25           /25           /25        /25
```

| Score | Grade | Interprétation |
|-------|-------|----------------|
| 90-100 | A | Excellent - Workspace bien optimisé |
| 75-89 | B | Bon - Quelques améliorations possibles |
| 60-74 | C | Moyen - Optimisations nécessaires |
| 40-59 | D | Mauvais - Actions urgentes requises |
| 0-39 | F | Critique - Refonte nécessaire |

### Trust Score (0-100)

```
Trust Score = (Data Quality Score + Process Reliability Score) / 2
```

| Score | Level | Interprétation |
|-------|-------|----------------|
| 80-100 | HIGH | Données fiables pour décisions |
| 60-79 | MEDIUM | Vérifier avant utilisation critique |
| 40-59 | LOW | Problèmes de fiabilité détectés |
| 0-39 | CRITICAL | Ne pas utiliser pour décisions |

---

## Utilisation

### Installation

```bash
cd pigment-agent-skills/reliability-audit
pip install -r requirements.txt
```

### Interface Web (recommandé)

```bash
python -m src.main --web
# Ouvrir http://127.0.0.1:8080
```

### Ligne de commande

```bash
# Minimum (CSV seul)
python -m src.main --executions data/Executions.csv

# Complet (tous les CSVs + APIs)
python -m src.main \
  --executions data/Executions.csv \
  --views data/Views.csv \
  --armset data/Armset_Upmset.csv \
  --metadata-key "pk_xxx" \
  --audit-key "ak_xxx"
```

### Options CLI

| Option | Description |
|--------|-------------|
| `--executions PATH` | Chemin vers Executions CSV |
| `--views PATH` | Chemin vers Views CSV |
| `--armset PATH` | Chemin vers Armset_Upmset CSV |
| `--metadata-key KEY` | Clé API Metadata |
| `--audit-key KEY` | Clé API Audit Logs |
| `--web` | Lancer l'interface web |
| `--port PORT` | Port pour l'interface web (défaut: 8080) |
| `--format FORMAT` | Format de sortie: csv, html, all |
| `--output-dir PATH` | Dossier de sortie |

---

## Interprétation des résultats

### Matrice de priorisation

```
                    IMPACT UTILISATEUR
                    Faible          Élevé
                 ┌─────────────┬─────────────┐
    Effort       │   IGNORER   │  QUICK WIN  │
    Faible       │             │  Priorité 1 │
                 ├─────────────┼─────────────┤
    Effort       │   BACKLOG   │  ROADMAP    │
    Élevé        │  Priorité 3 │  Priorité 2 │
                 └─────────────┴─────────────┘
```

### Quick Wins typiques

| Problème détecté | Action |
|------------------|--------|
| Metrics non scopées > 5s | Activer le scoping avec BY/FILTER |
| Views lentes très utilisées | Ajouter page selectors |
| ARM/UPM > 20% du compute | Réduire dimensions dans access rights |
| Metrics > 10 dimensions | Convertir en Properties |

### Roadmap typique

| Problème détecté | Action |
|------------------|--------|
| Blocks > 10M lignes | Splitter le block |
| Application monolithique | Découper en applications |
| Versions > 2 ans | Archiver les anciennes versions |
| Formules avec PREVIOUS() en chaîne | Revoir la logique |

### Signaux d'alerte critiques

| Signal | Signification | Action immédiate |
|--------|---------------|------------------|
| 🚨 Trust Level CRITICAL | Données non fiables | Stopper l'utilisation pour décisions |
| 🚨 Metrics > 30s | Timeout probable | Optimiser ou splitter |
| 🚨 Batch missing > 5 days | Process cassé | Vérifier scheduler |
| 🚨 Performance degrading | Régression | Analyser changements récents |

---

## Structure du projet

```
reliability-audit/
├── README.md                 # Cette documentation
├── requirements.txt          # Dépendances Python
├── config/
│   ├── thresholds.yaml       # Seuils configurables
│   └── config.example.yaml   # Configuration exemple
├── sample-data/              # Données de test
│   ├── Executions_anonymized_basic.csv
│   ├── Views_Executions_anonymized_basic.csv
│   └── Armset_Upmset_Executions_anonymized_basic.csv
├── src/
│   ├── main.py               # Point d'entrée CLI
│   ├── web.py                # Interface web Flask
│   ├── config.py             # Chargement configuration
│   ├── data_loader.py        # Chargement CSV
│   ├── scoring.py            # Calcul des scores
│   ├── report_generator.py   # Génération rapports
│   ├── api_client.py         # Clients API Pigment
│   └── analyzers/
│       ├── performance_analyzer.py
│       ├── scoping_analyzer.py
│       ├── complexity_analyzer.py
│       ├── workload_analyzer.py
│       ├── access_rights_analyzer.py
│       ├── data_quality_analyzer.py
│       ├── usage_analyzer.py
│       ├── version_analyzer.py
│       └── permission_analyzer.py
└── output/                   # Rapports générés
```

---

## FAQ

### Q: Quelle est la différence entre Performance Score et Trust Score ?

**Performance Score** mesure la rapidité et l'optimisation technique.
**Trust Score** mesure si on peut se fier aux données pour prendre des décisions.

Un workspace peut être rapide (Performance A) mais avec des données obsolètes (Trust LOW).

### Q: Comment obtenir les fichiers CSV ?

Les fichiers CSV sont exportés depuis l'interface admin Pigment ou via l'API Export.
Contactez votre administrateur Pigment pour obtenir l'accès.

### Q: À quelle fréquence faire l'audit ?

| Type d'audit | Fréquence | Déclencheur |
|--------------|-----------|-------------|
| Quick check | Hebdomadaire | Automatique |
| Standard | Mensuel | Routine |
| Complet | Trimestriel | Ou après changement majeur |

### Q: Comment customiser les seuils ?

Modifiez `config/thresholds.yaml`:

```yaml
performance:
  metric_execution:
    watch: 3000      # Ajuster selon contexte
    warning: 5000
    critical: 30000
```
