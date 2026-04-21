"""
Formula Service - Database-Driven Formula Management
====================================================

This service provides a centralized way to load and manage formulas.
It implements a hybrid approach:
1. Load from database first (if available)
2. Fall back to Python files for backward compatibility
3. Cache for performance

ENHANCED FEATURES:
- Database-first formula loading
- Fallback to Python files (renewable_energy_complete_formulas.py)
- Caching for performance
- Formula validation
- Version control support
"""

from typing import Dict, Optional, List, Tuple
from django.db import models
from django.core.cache import cache
from django.utils import timezone
import logging
import re
from functools import lru_cache

from simulator.models import (
    Formula,
    FormulaVariable,
    LandUse,
    RenewableData,
    VerbrauchData,
)

logger = logging.getLogger(__name__)

_PATTERN_VERBRAUCH = re.compile(
    r'[Vv]erbrauch_([0-9\._]+?)(?:_(status|ziel|target))?(?![a-zA-Z0-9\._])'
)
_PATTERN_RENEWABLE = re.compile(
    r'[Rr]enewable_([0-9\._]+?)(?:_(status|target|value))?(?![a-zA-Z0-9\._])'
)
_PATTERN_LANDUSE = re.compile(
    r'[Ll]andUse_([A-Za-z0-9\._]+?)(?:_(status|target))?(?![a-zA-Z0-9\._])'
)
_PATTERN_BARE = re.compile(
    r'\b[1-9]\d*(?:\.\d+)+(?:_(?:target|ziel|status))?\b'
)
_PATTERN_WS = re.compile(r'WS_(\d+)_(\w+)')

@lru_cache(maxsize=2048)
def _extract_auto_tokens(expression: str):
    """
    Parse expression once and cache token structure.
    Safe optimization: only parsing is cached (no values).
    """
    verbrauch_tokens = []
    for match in _PATTERN_VERBRAUCH.finditer(expression):
        token = match.group(0)
        code_raw = match.group(1).strip('_').strip('.')
        suffix = match.group(2)
        verbrauch_tokens.append((token, code_raw, suffix))

    renewable_tokens = []
    for match in _PATTERN_RENEWABLE.finditer(expression):
        token = match.group(0)
        code_raw = match.group(1).strip('_').strip('.')
        suffix = match.group(2)
        renewable_tokens.append((token, code_raw, suffix))

    landuse_tokens = []
    for match in _PATTERN_LANDUSE.finditer(expression):
        token = match.group(0)
        code_raw = match.group(1).strip('_').strip('.')
        suffix = match.group(2)
        landuse_tokens.append((token, code_raw, suffix))

    bare_tokens = tuple(set(_PATTERN_BARE.findall(expression)))
    ws_tokens = tuple((m.group(0), int(m.group(1)), m.group(2)) for m in _PATTERN_WS.finditer(expression))
    ws_constant_names = tuple(
        name for name in ('ETA_STROM_GAS', 'ETA_GAS_STROM', 'ABREGELUNG_THRESHOLD')
        if name in expression
    )

    return (
        tuple(verbrauch_tokens),
        tuple(renewable_tokens),
        tuple(landuse_tokens),
        bare_tokens,
        ws_tokens,
        ws_constant_names,
    )

def evaluate_formula_by_key(formula_key: str, extra_context: Optional[Dict] = None) -> Optional[float]:
    """
    Evaluate a formula by its key using FormulaVariable mappings to resolve inputs.

    Returns:
        float or None if not found/failed.
    """
    formula = Formula.objects.filter(key=formula_key).prefetch_related("variables").first()
    if not formula:
        return None

    context = _build_context(formula)
    if extra_context:
        context.update(extra_context)

    try:
        return _safe_eval(formula.expression, context, formula_key=formula_key)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"Error evaluating formula '{formula_key}': {exc}")
        return None

def _build_context(formula: Formula, use_target: bool = False, status_lookup: Optional[Dict] = None, target_lookup: Optional[Dict] = None) -> Dict[str, float]:
    """
    Resolve all variables for a formula into a plain dict.

    Args:
        formula: The Formula object
        use_target: If True, resolve variables using target/ziel values instead of status
    """
    context: Dict[str, float] = {}
    for var in formula.variables.all():
        use_var_target = use_target or ('ziel' in var.source_type.lower() or 'target' in var.source_type.lower())

        resolved = _resolve_variable(var, use_target=use_var_target, status_lookup=status_lookup, target_lookup=target_lookup)
        if resolved is None:
            resolved = var.default_value
        if resolved is None:
            # No value available; use 0 to keep evaluation resilient
            resolved = 0
        context[var.variable_name] = resolved
    return context

def _resolve_variable(var: FormulaVariable, use_target: bool = False) -> Optional[float]:
    """
    Resolve a single FormulaVariable to a numeric value.
    
    IMPORTANT: The source_type determines which field to read:
    - verbrauch_status -> always read .status field
    - verbrauch_ziel -> always read .ziel field
    The use_target parameter is NOT used for verbrauch (it's for landuse/renewable)
    """
    source_key = var.source_key

    if var.source_type == FormulaVariable.LITERAL:
        try:
            return float(source_key)
        except (TypeError, ValueError):
            return None

    # FIXED: source_type determines the field, NOT use_target!
    if var.source_type == FormulaVariable.LANDUSE_STATUS:
        # Always read status_ha field
        return _get_value(LandUse, "code", source_key, "status_ha")
    if var.source_type == FormulaVariable.LANDUSE_TARGET:
        # Always read target_ha field
        return _get_value(LandUse, "code", source_key, "target_ha")
    if var.source_type == FormulaVariable.RENEWABLE_STATUS:
        # Always read status_value field
        return _get_value(RenewableData, "code", source_key, "status_value")
    if var.source_type == FormulaVariable.RENEWABLE_TARGET:
        # Always read target_value field
        return _get_value(RenewableData, "code", source_key, "target_value")
    
    if var.source_type == FormulaVariable.VERBRAUCH_STATUS:
        # Always read status field
        return _get_value(VerbrauchData, "code", source_key, "status")
    if var.source_type == FormulaVariable.VERBRAUCH_ZIEL:
        # Always read ziel field
        return _get_value(VerbrauchData, "code", source_key, "ziel")

    return None

def _get_value(model: models.Model, lookup_field: str, lookup_value: str, value_field: str) -> Optional[float]:
    """Helper to fetch a numeric field from a model instance."""
    try:
        obj = model.objects.only(value_field).get(**{lookup_field: lookup_value})
        return getattr(obj, value_field)
    except model.DoesNotExist:
        return None
    except Exception:
        return None

def _preprocess_if_syntax(expression: str) -> str:
    """
    Convert Excel-style IF(condition;true;false) to Python-compatible IF(condition,true,false).
    Keeps commas intact; only replaces semicolons inside IF(...) blocks.
    """
    if "IF(" not in expression and ";" not in expression:
        return expression
    # Simplest robust approach: all semicolons become commas
    return expression.replace(";", ",")

def _normalize_target_tokens(expression: str) -> str:
    """
    Normalize target/ziel tokens like LandUse_LU_2.1_ziel -> LandUse_LU_2.1.
    This keeps expressions consistent while allowing target values to be resolved.
    """
    if not expression or ("_ziel" not in expression and "_target" not in expression):
        return expression
    patterns = [
        r'\b(LandUse_[A-Za-z0-9_.]+)_(ziel|target)\b',
        r'\b(Renewable_[0-9_.]+)_(ziel|target)\b',
        r'\b(Verbrauch_[0-9_.]+)_(ziel|target)\b',
        r'\b(RenewableData_[0-9.]+)_(ziel|target)\b',
        r'\b(VerbrauchData_[0-9.]+)_(ziel|target)\b',
    ]
    for pattern in patterns:
        expression = re.sub(pattern, r'\1', expression)
    return expression

_WS_DAILY_FIELD_ALIASES = {
    "stromverbr": "stromverbrauch",
    "stromverbr_raumwaerm_korr": "stromverbr_raumw_korr",
    "solarstrom": "solar_strom",
    "windstrom": "wind_strom",
    "sonst_kraft_konstant": "sonst_kraftw",
    "abregelung_z": "abregelung",
    "ladezust_burtto": "ladezust_brutto",
    "ladezustand_netto": "ladezust_netto",
}

_WS_366_CURRENT_ALIASES = {
    "einspeich": "einspeich_sum",
    "abregelung": "abregelung_sum",
    "abregelung_z": "abregelung_sum",
    "ausspeich_rueckverstr": "ausspeich_sum",
    "ladezust_netto": "storage_drift",
    "ladezustand_netto": "storage_drift",
}

def _map_ws_daily_field(source_key: str) -> str:
    return _WS_DAILY_FIELD_ALIASES.get(source_key, source_key)

def _ws365_value_from_snapshot(ws_snapshot: Dict, row_num: int, source_key: str) -> float:
    if not ws_snapshot:
        return 0.0

    source_key = (source_key or "").strip()
    daily_data = ws_snapshot.get("daily_data") or []
    current = ws_snapshot.get("current") or {}

    if 1 <= int(row_num or 0) <= 365:
        idx = int(row_num) - 1
        if idx >= len(daily_data):
            return 0.0
        row = daily_data[idx] or {}
        field = _map_ws_daily_field(source_key)
        return float(row.get(field) or 0)

    if int(row_num or 0) == 366:
        if source_key in {"stromverbr_raumwaerm_korr", "stromverbr"}:
            from simulator.signals import compute_ws_diagram_reference

            diagram = compute_ws_diagram_reference(use_ws_overrides=False)
            return float(diagram.get("stromverbr_raumwaerm_korr_366") or 0)

        current_field = _WS_366_CURRENT_ALIASES.get(source_key, source_key)
        return float(current.get(current_field) or 0)

    return 0.0

def _ws365_sum_from_snapshot(ws_snapshot: Dict, source_key: str) -> float:
    if not ws_snapshot:
        return 0.0

    source_key = (source_key or "").strip()
    current = ws_snapshot.get("current") or {}
    daily_data = ws_snapshot.get("daily_data") or []

    sum_aliases = {
        "einspeich": "einspeich_sum",
        "abregelung": "abregelung_sum",
        "abregelung_z": "abregelung_sum",
        "ausspeich_rueckverstr": "ausspeich_sum",
        "ueberschuss_strom": "ueberschuss_sum",
        "solarstrom": "solar_strom_sum",
        "windstrom": "wind_strom_sum",
    }
    sum_key = sum_aliases.get(source_key)
    if sum_key:
        return float(current.get(sum_key) or 0)

    mapped_key = _map_ws_daily_field(source_key)
    total = 0.0
    for row in daily_data:
        if not isinstance(row, dict):
            continue
        total += float(row.get(mapped_key) or 0)
    return total

def _auto_context_from_tokens(
    expression: str,
    use_target: bool,
    *,
    verbrauch_status_lookup: Optional[Dict[str, float]] = None,
    verbrauch_target_lookup: Optional[Dict[str, float]] = None,
    renewable_status_lookup: Optional[Dict[str, float]] = None,
    renewable_target_lookup: Optional[Dict[str, float]] = None,
    landuse_status_lookup: Optional[Dict[str, float]] = None,
    landuse_target_lookup: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Build a context dict by resolving Verbrauch_/Renewable_/LandUse_ tokens found
    in the expression.
    """
    from simulator.models import LandUse, RenewableData, VerbrauchData
    context: Dict[str, float] = {}

    (
        verbrauch_tokens,
        renewable_tokens,
        landuse_tokens,
        bare_tokens,
        ws_tokens,
        ws_constant_names,
    ) = _extract_auto_tokens(expression)

    verbrauch_cache: Dict[Tuple[str, bool], float] = {}
    renewable_cache: Dict[Tuple[str, bool], float] = {}
    landuse_cache: Dict[Tuple[str, bool], float] = {}
    ws_snapshot: Optional[Dict] = None
    if ws_tokens:
        try:
            from simulator.ws_365_service import get_ws_365_data

            ws_snapshot = get_ws_365_data(run_goal_seek=False)
        except Exception:
            ws_snapshot = None

    # 1. Verbrauch tokens
    for token, code_raw, suffix in verbrauch_tokens:
        
        token_use_target = use_target
        if suffix in ['ziel', 'target']:
            token_use_target = True
        elif suffix == 'status':
            token_use_target = False
            
        # Try exact code first, then try with dots
        codes_to_try = [code_raw, code_raw.replace("_", ".")]
        
        value = 0
        for code in codes_to_try:
            if token_use_target and verbrauch_target_lookup is not None and code in verbrauch_target_lookup:
                value = float(verbrauch_target_lookup.get(code) or 0)
                break
            if (not token_use_target) and verbrauch_status_lookup is not None and code in verbrauch_status_lookup:
                value = float(verbrauch_status_lookup.get(code) or 0)
                break
            key = (code, token_use_target)
            if key in verbrauch_cache:
                value = verbrauch_cache[key]
                break
            try:
                obj = VerbrauchData.objects.only("status", "ziel").get(code=code)
                value = float((obj.ziel if token_use_target else obj.status) or 0)
                verbrauch_cache[key] = value
                break
            except (VerbrauchData.DoesNotExist, ValueError):
                continue
        context[token] = value

    # 2. Renewable tokens
    for token, code_raw, suffix in renewable_tokens:
        
        token_use_target = use_target
        if suffix == 'target':
            token_use_target = True
        elif suffix == 'status':
            token_use_target = False
            
        codes_to_try = [code_raw, code_raw.replace("_", ".")]
        value = 0
        for code in codes_to_try:
            if token_use_target and renewable_target_lookup is not None and code in renewable_target_lookup:
                value = float(renewable_target_lookup.get(code) or 0)
                break
            if (not token_use_target) and renewable_status_lookup is not None and code in renewable_status_lookup:
                value = float(renewable_status_lookup.get(code) or 0)
                break
            key = (code, token_use_target)
            if key in renewable_cache:
                value = renewable_cache[key]
                break
            try:
                obj = RenewableData.objects.only("status_value", "target_value").get(code=code)
                value = float((obj.target_value if token_use_target else obj.status_value) or 0)
                renewable_cache[key] = value
                break
            except (RenewableData.DoesNotExist, ValueError):
                continue
        context[token] = value

    # 3. LandUse tokens
    for token, code_raw, suffix in landuse_tokens:
        
        token_use_target = use_target
        if suffix == 'target':
            token_use_target = True
        elif suffix == 'status':
            token_use_target = False
            
        # LandUse codes can be complex (LU_2.1)
        codes_to_try = [code_raw, code_raw.replace("_", ".")]
        value = 0
        for code in codes_to_try:
            if token_use_target and landuse_target_lookup is not None and code in landuse_target_lookup:
                value = float(landuse_target_lookup.get(code) or 0)
                break
            if (not token_use_target) and landuse_status_lookup is not None and code in landuse_status_lookup:
                value = float(landuse_status_lookup.get(code) or 0)
                break
            key = (code, token_use_target)
            if key in landuse_cache:
                value = landuse_cache[key]
                break
            try:
                obj = LandUse.objects.only("status_ha", "target_ha").get(code=code)
                value = float((obj.target_ha if token_use_target else obj.status_ha) or 0)
                landuse_cache[key] = value
                break
            except LandUse.DoesNotExist:
                continue
        context[token] = value

    for token in bare_tokens:
        if token not in context:
            try:
                # Handle suffix
                base_code = token
                is_target = use_target
                if token.endswith('_target') or token.endswith('_ziel'):
                    base_code = token.rsplit('_', 1)[0]
                    is_target = True
                elif token.endswith('_status'):
                    base_code = token.rsplit('_', 1)[0]
                    is_target = False

                if is_target and renewable_target_lookup is not None and base_code in renewable_target_lookup:
                    context[token] = float(renewable_target_lookup.get(base_code) or 0)
                    continue
                if (not is_target) and renewable_status_lookup is not None and base_code in renewable_status_lookup:
                    context[token] = float(renewable_status_lookup.get(base_code) or 0)
                    continue
                
                key = (base_code, is_target)
                if key in renewable_cache:
                    context[token] = renewable_cache[key]
                else:
                    obj = RenewableData.objects.only("status_value", "target_value").get(code=base_code)
                    val = float((obj.target_value if is_target else obj.status_value) or 0)
                    renewable_cache[key] = val
                    context[token] = val
            except RenewableData.DoesNotExist:
                context[token] = 0

    for token, row_num, column_name in ws_tokens:
        if token not in context:  # Don't overwrite if already set
            try:
                context[token] = _ws365_value_from_snapshot(ws_snapshot, row_num, column_name)
            except Exception:
                context[token] = 0

    for const_name in ws_constant_names:
        if const_name not in context:
            try:
                from simulator.signals import get_ws_constants
                ws_consts = get_ws_constants()
                context[const_name] = ws_consts.get(const_name, 0)
            except Exception:
                # Default values if get_ws_constants fails
                defaults = {'ETA_STROM_GAS': 0.65, 'ETA_GAS_STROM': 0.585, 'ABREGELUNG_THRESHOLD': 200}
                context[const_name] = defaults.get(const_name, 0)

    return context

def _safe_eval(expression: str, names: Dict[str, float], use_target: bool = False, formula_key: str = "unknown") -> Optional[float]:
    """
    Evaluate a math expression safely using a controlled names dict.
    Supports +, -, *, /, parentheses, IF(), and basic helpers (max/min/abs/round).
    
    STABILITY: Automatically prefixes naked numeric tokens (e.g., 2_7_ziel -> Verbrauch_2_7_ziel)
    to avoid SyntaxErrors.
    """
    if not expression:
        return None

    # 1. Normalize IF syntax and trim whitespace
    expression = _preprocess_if_syntax(expression.strip())
    
    naked_pattern = r'\b([0-9]+(?:_[0-9]+)+(?:_ziel|_status|_target)?)\b'
    def prefix_token(match):
        t = match.group(1)
        if t in (names or {}): return t
        # If it's a pure number (no underscores), leave it alone
        if "_" not in t: return t
        return f"Verbrauch_{t}"
    expression = re.sub(naked_pattern, prefix_token, expression)

    expression = _normalize_target_tokens(expression)

    auto_ctx = _auto_context_from_tokens(expression, use_target=use_target)
    
    scope = {"__builtins__": {}}
    scope.update({
        "max": max,
        "min": min,
        "abs": abs,
        "round": round,
        "IF": lambda cond, t, f: t if cond else f,
    })
    if names:
        scope.update(names)
    
    # Fill gaps from auto-resolution
    for k, v in auto_ctx.items():
        scope.setdefault(k, v)

    for token, value in sorted(scope.items(), key=lambda kv: len(kv[0]), reverse=True):
        if isinstance(value, (int, float)):
            if re.match(r'^[0-9]', token) or "." in token:
                pattern = r'(?<![0-9.])' + re.escape(token) + r'(?![0-9.])'
                expression = re.sub(pattern, str(value), expression)

    try:
        result = eval(expression, scope, {})
        return float(result)
    except ZeroDivisionError:
        return 0
    except Exception as e:
        logger.error(f"Safe eval failed for '{formula_key}': {e} | Expr: {expression}")
        return None

class FormulaService:
    """
    Centralized formula management service.
    Loads formulas from database with fallback to Python files.
    """
    
    CACHE_PREFIX = 'formula_'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, use_cache=True):
        """
        Initialize the formula service.
        
        Args:
            use_cache: Whether to use Django cache for formulas
        """
        self.use_cache = use_cache
    
    def get_formula(self, key: str, category: str = 'renewable') -> Optional[Dict]:
        """
        Get formula definition by key.
        
        100% DATABASE-DRIVEN - NO PYTHON FALLBACKS!
        
        Args:
            key: Formula key (e.g., '1.1.2.1.2')
            category: Formula category (renewable, verbrauch, landuse, etc.)
            
        Returns:
            Dictionary with formula details or None if not found
        """
        # Try cache first
        if self.use_cache:
            cached = cache.get(f'{self.CACHE_PREFIX}{key}')
            if cached is not None:
                return cached
        
        # Load from database ONLY - no fallbacks
        formula = self._get_from_database(key, category)
        if formula:
            if self.use_cache:
                cache.set(f'{self.CACHE_PREFIX}{key}', formula, self.CACHE_TIMEOUT)
            return formula
        
        # No formula found - return None (caller must handle)
        return None
    
    def _get_from_database(self, key: str, category: str) -> Optional[Dict]:
        """Load formula from database"""
        try:
            formula_obj = Formula.objects.filter(
                key=key,
                is_active=True
            ).first()
            
            if formula_obj:
                return {
                    'key': formula_obj.key,
                    'expression': formula_obj.expression,
                    'description': formula_obj.description,
                    'is_active': formula_obj.is_active,
                    'is_fixed': formula_obj.is_fixed,
                    'category': formula_obj.category,
                    'version': formula_obj.version,
                    'validation_status': formula_obj.validation_status,
                }
        except Exception as e:
            logger.warning(f"Error loading formula {key} from database: {e}")
        
        return None
    
    def get_all_formulas(self, category: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """
        Get all formulas from database ONLY.
        
        100% DATABASE-DRIVEN - NO PYTHON FILE FALLBACKS!
        
        Args:
            category: Filter by category (renewable, verbrauch, etc.)
            active_only: Only return active formulas
            
        Returns:
            List of formula dictionaries
        """
        formulas = []
        
        # Get from database ONLY - no Python file fallbacks
        try:
            queryset = Formula.objects.all()
            if active_only:
                queryset = queryset.filter(is_active=True)
            if category:
                queryset = queryset.filter(category=category)
            
            for formula_obj in queryset:
                formulas.append({
                    'key': formula_obj.key,
                    'expression': formula_obj.expression,
                    'description': formula_obj.description,
                    'is_active': formula_obj.is_active,
                    'is_fixed': formula_obj.is_fixed,
                    'category': formula_obj.category,
                    'version': formula_obj.version,
                    'validation_status': formula_obj.validation_status,
                })
        except Exception as e:
            logger.error(f"Error loading formulas from database: {e}")
            raise ValueError(f"Cannot load formulas from database. Please import formulas first. Error: {e}")
        
        return formulas
    
    def save_formula(self, key: str, expression: str, description: str = '', 
                    category: str = 'renewable', is_fixed: bool = False) -> bool:
        """
        Save or update a formula in the database.
        
        Args:
            key: Formula key
            expression: Formula expression
            description: Human-readable description
            category: Formula category
            is_fixed: Whether this is a fixed value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            formula, created = Formula.objects.update_or_create(
                key=key,
                defaults={
                    'expression': expression,
                    'description': description,
                    'category': category,
                    'is_fixed': is_fixed,
                    'is_active': True,
                    'validation_status': 'pending',
                }
            )
            
            if not created:
                formula.increment_version()
            
            # Invalidate cache
            if self.use_cache:
                cache.delete(f'{self.CACHE_PREFIX}{key}')
            
            logger.info(f"{'Created' if created else 'Updated'} formula {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving formula {key}: {e}")
            return False
    
    def clear_cache(self, key: Optional[str] = None):
        """
        Clear cached formulas.
        
        Args:
            key: Specific formula key to clear, or None to clear all
        """
        if self.use_cache:
            if key:
                # Clear specific formula
                cache.delete(f'{self.CACHE_PREFIX}{key}')
                logger.info(f"Formula cache cleared for {key}")
            else:
                # Clear all formulas
                try:
                    cache.delete_pattern(f'{self.CACHE_PREFIX}*')
                except:
                    pass
                logger.info("All formula cache cleared")

# Global instance for easy access
_formula_service = None

def get_formula_service() -> FormulaService:
    """Get or create global FormulaService instance"""
    global _formula_service
    if _formula_service is None:
        _formula_service = FormulaService()
    return _formula_service

def evaluate_with_mappings(
    formula_key: str,
    category: str = 'renewable',
    status_lookup: Optional[Dict] = None,
    target_lookup: Optional[Dict] = None,
    formula_obj: Optional[Formula] = None,
) -> tuple:
    """
    NEW: Evaluate formula using FormulaVariable mappings.
    This is the FULLY EXTENSIBLE approach.
    
    Returns:
        tuple: (status_value, target_value) or (None, None)
    """
    if formula_obj is not None:
        formula = formula_obj
    else:
        try:
            formula = Formula.objects.prefetch_related('variables').get(
                key=formula_key,
                category=category,
                is_active=True
            )
        except Formula.DoesNotExist:
            return None, None
    
    # Determine if this is a target/ziel formula
    is_target_formula = (
        formula.formula_type == 'ziel'
        or formula_key.endswith('_ziel')
        or formula_key.endswith('_target')
    )
    
    context = _build_context(formula, use_target=is_target_formula, status_lookup=status_lookup, target_lookup=target_lookup)  # use_target affects token auto-resolution
    
    # Evaluate the formula
    result = _safe_eval(formula.expression, context, use_target=is_target_formula, formula_key=formula_key)
    
    # Return based on formula type
    if is_target_formula:
        return (None, result)
    else:
        return (result, None)

def _resolve_variable(var, use_target: bool = False, status_lookup: Optional[Dict] = None, target_lookup: Optional[Dict] = None):
    """
    Resolve a FormulaVariable to its numeric value.
    PRIORITIZES IN-MEMORY LOOKUPS over database fetches.
    """
    source_key = var.source_key
    
    # Literal number
    if var.source_type == 'literal':
        try:
            return float(source_key)
        except (TypeError, ValueError):
            return var.default_value
            
    # CHECK LOOKUPS FIRST (Fast Path)
    if status_lookup is not None and target_lookup is not None:
        def _lookup_from_map(lookup_map, keys, dict_field=None):
            for key in keys:
                if key in lookup_map:
                    value = lookup_map[key]
                    if isinstance(value, dict):
                        if dict_field:
                            return value.get(dict_field, 0)
                        return value.get('value', 0)
                    return value
            return None

        # VerbrauchData (direct or code references)
        if var.source_type in ['verbrauch_status', 'verbrauch_ziel', 'verbrauch_code_status', 'verbrauch_code_ziel']:
            use_target_lookup = var.source_type in ['verbrauch_ziel', 'verbrauch_code_ziel']
            lookup = target_lookup if use_target_lookup else status_lookup
            verbrauch_keys = (
                source_key,
                f"Verbrauch_{source_key}",
                f"Verbrauch_{source_key.replace('.', '_')}",
            )
            cached_value = _lookup_from_map(lookup, verbrauch_keys)
            if cached_value is not None:
                return cached_value

        # RenewableData (direct or code references)
        if var.source_type in ['renewable_status', 'renewable_target', 'renewable_code_status', 'renewable_code_target']:
            use_target_lookup = var.source_type in ['renewable_target', 'renewable_code_target']
            lookup = target_lookup if use_target_lookup else status_lookup
            renewable_keys = (
                source_key,
                f"Renewable_{source_key}",
                f"RenewableData_{source_key}",
            )
            cached_value = _lookup_from_map(
                lookup,
                renewable_keys,
                dict_field='target_value' if use_target_lookup else 'status_value',
            )
            if cached_value is not None:
                return cached_value

        # LandUse
        if var.source_type in ['landuse_status', 'landuse_target']:
            use_target_lookup = var.source_type == 'landuse_target'
            lookup = target_lookup if use_target_lookup else status_lookup
            clean_key = source_key.replace('LU_', '') if source_key.startswith('LU_') else source_key
            landuse_keys = (
                source_key,
                clean_key,
                f"LandUse_{source_key}",
                f"LandUse_{clean_key}",
            )
            cached_value = _lookup_from_map(
                lookup,
                landuse_keys,
                dict_field='target_ha' if use_target_lookup else 'status_ha',
            )
            if cached_value is not None:
                return cached_value

    # SLOW PATH - Database Fallback
    
    # LandUse
    if var.source_type == 'landuse_status':
        from simulator.models import LandUse
        return _get_value(LandUse, 'code', source_key, 'status_ha') or var.default_value
    if var.source_type == 'landuse_target':
        from simulator.models import LandUse
        return _get_value(LandUse, 'code', source_key, 'target_ha') or var.default_value
    
    # RenewableData
    if var.source_type == 'renewable_status':
        from simulator.models import RenewableData
        return _get_value(RenewableData, 'code', source_key, 'status_value') or var.default_value
    if var.source_type == 'renewable_target':
        from simulator.models import RenewableData
        return _get_value(RenewableData, 'code', source_key, 'target_value') or var.default_value
    
    # RenewableData CODE reference
    if var.source_type in ['renewable_code_status', 'renewable_code_target']:
        from simulator.models import RenewableData
        try:
            renewable = RenewableData.objects.get(code=source_key)
            if not renewable.is_fixed:
                status_calc, target_calc = renewable.get_calculated_values()
                return target_calc if use_target else status_calc
            else:
                return renewable.target_value if use_target else renewable.status_value
        except RenewableData.DoesNotExist:
            return var.default_value or 0
        except Exception as e:
            return var.default_value or 0
    
    # VerbrauchData
    if var.source_type in ['verbrauch_status', 'verbrauch_ziel']:
        from simulator.models import VerbrauchData
        field = 'ziel' if var.source_type == 'verbrauch_ziel' else 'status'
        return _get_value(VerbrauchData, 'code', source_key, field) or var.default_value
    
    # VerbrauchData CODE reference
    if var.source_type in ['verbrauch_code_status', 'verbrauch_code_ziel']:
        from simulator.models import VerbrauchData
        try:
            verbrauch = VerbrauchData.objects.get(code=source_key)
            if verbrauch.is_calculated:
                status_calc, ziel_calc = verbrauch.get_calculated_values()
                return ziel_calc if use_target else status_calc
            else:
                return verbrauch.ziel if use_target else verbrauch.status
        except VerbrauchData.DoesNotExist:
            return var.default_value or 0
        except Exception as e:
            return var.default_value or 0
    
    # WS-specific source types
    if var.source_type == 'ws_row_value':
        return var.default_value or 0
    
    if var.source_type == FormulaVariable.WS_ANNUAL_SUMMARY or str(var.source_type).endswith('_366'):
        # Compatibility mapping to WS 365 annual aggregate values.
        try:
            from simulator.ws_365_service import get_ws_365_data

            ws_snapshot = get_ws_365_data(run_goal_seek=False)
            return _ws365_value_from_snapshot(ws_snapshot, 366, source_key)
        except Exception:
            return var.default_value or 0

    if var.source_type == 'ws_sum':
        # Sum of column for days 1-365 from WS 365 service output.
        try:
            from simulator.ws_365_service import get_ws_365_data

            ws_snapshot = get_ws_365_data(run_goal_seek=False)
            return _ws365_sum_from_snapshot(ws_snapshot, source_key)
        except Exception:
            return var.default_value or 0
    
    if var.source_type == 'ws_day_prev':
        return var.default_value or 0
    
    return var.default_value

def _get_value(model, lookup_field, lookup_value, value_field):
    """Helper to safely get a value from a model."""
    try:
        obj = model.objects.only(value_field).get(**{lookup_field: lookup_value})
        val = getattr(obj, value_field)
        return float(val) if val is not None else None
    except (model.DoesNotExist, ValueError, TypeError):
        return None
