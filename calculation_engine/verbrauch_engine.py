"""
Verbrauch Calculator - 100% Database-Driven Energy Consumption Calculations
===========================================================================

FULLY EXTENSIBLE - ALL FORMULAS FROM DATABASE!

This provides:
- Editable formulas via Django Admin
- Real-time formula updates without code changes
- Versioning and validation
- NO hardcoded formulas - database only!
"""

from .formula_evaluator import FormulaEvaluator
from simulator.formula_service import FormulaService

class VerbrauchCalculator:
    """
    Calculator for energy consumption (Verbrauch) data.
    100% DATABASE-DRIVEN - NO PYTHON FILE FALLBACKS!
    """
    
    def __init__(self):
        self.evaluator = FormulaEvaluator()
        self.formula_service = FormulaService(use_cache=True)
        self.cache = {}
        self._formula_cache = {}
        self._target_formula_cache = {}
    
    def set_data_sources(self, verbrauch_data, renewable_data=None, landuse_data=None):
        """
        Set up lookup dictionaries from data sources.
        
        Args:
            verbrauch_data: Dict of {code: {'status': x, 'ziel': y}}
            renewable_data: Optional dict of renewable data
            landuse_data: Optional dict of landuse data
        """
        # Clear cache when new data sources are set
        self.cache = {}
        
        status_lookup = {}
        target_lookup = {}
        
        for code, data in verbrauch_data.items():
            code_with_underscores = code.replace('.', '_')
            verbrauch_key_underscore = f'Verbrauch_{code_with_underscores}'
            verbrauch_key_dot = f'Verbrauch_{code}'
            if data.get('status') is not None:
                status_lookup[verbrauch_key_underscore] = float(data['status'])
                status_lookup[verbrauch_key_dot] = float(data['status'])
            if data.get('ziel') is not None:
                target_lookup[verbrauch_key_underscore] = float(data['ziel'])
                target_lookup[verbrauch_key_dot] = float(data['ziel'])
        
        # Add RenewableData if provided
        if renewable_data:
            for code, data in renewable_data.items():
                renewable_key = f'Renewable_{code}'
                if data.get('status_value') is not None:
                    status_lookup[renewable_key] = float(data['status_value'])
                if data.get('target_value') is not None:
                    target_lookup[renewable_key] = float(data['target_value'])
        
        # Add LandUse if provided
        if landuse_data:
            for code, data in landuse_data.items():
                # Convert LU_1.1 -> 1.1, LU_2.1 -> 2.1, etc.
                clean_code = code.replace('LU_', '') if code.startswith('LU_') else code
                landuse_key = f'LandUse_{clean_code}'
                if data.get('status_ha') is not None:
                    status_lookup[landuse_key] = float(data['status_ha'])
                if data.get('target_ha') is not None:
                    target_lookup[landuse_key] = float(data['target_ha'])
        
        self.evaluator.set_lookups(status_lookup, target_lookup)
    
    def calculate(self, code):
        """
        Calculate status and ziel values for a verbrauch item.
        Uses FormulaVariable mappings if available, else falls back to expression-based calculation.
        
        Args:
            code: The verbrauch code (e.g., '1.2.1' or 'V_1.2.1')
            
        Returns:
            tuple: (status, ziel) values or (None, None) if fixed or error
        """
        lookup_code = f'V_{code}' if not code.startswith('V_') else code
        
        # Check cache
        if lookup_code in self.cache:
            return self.cache[lookup_code]
        
        # TRY 1: Use FormulaVariable mappings (fully extensible)
        from simulator.formula_service import evaluate_with_mappings
        from simulator.models import Formula

        status_lookup = self.evaluator.status_lookup
        target_lookup = self.evaluator.target_lookup

        formula_obj = self._formula_cache.get(lookup_code, "__MISS__")
        if formula_obj == "__MISS__":
            formula_obj = Formula.objects.filter(
                key=lookup_code, category='verbrauch', is_active=True
            ).prefetch_related("variables").first()
            self._formula_cache[lookup_code] = formula_obj

        # Try to get status from base formula
        status, _ = evaluate_with_mappings(
            lookup_code,
            category='verbrauch',
            status_lookup=status_lookup,
            target_lookup=target_lookup,
            formula_obj=formula_obj,
        )

        # Try to get ziel from _ziel formula (separate formula)
        ziel_key = f'{lookup_code}_ziel'
        ziel_formula_obj = self._target_formula_cache.get(ziel_key, "__MISS__")
        if ziel_formula_obj == "__MISS__":
            ziel_formula_obj = Formula.objects.filter(
                key=ziel_key, category='verbrauch', is_active=True
            ).prefetch_related("variables").first()
            self._target_formula_cache[ziel_key] = ziel_formula_obj

        _, ziel = evaluate_with_mappings(
            ziel_key,
            category='verbrauch',
            status_lookup=status_lookup,
            target_lookup=target_lookup,
            formula_obj=ziel_formula_obj,
        )
        
        if ziel is None and status is not None:
            _, ziel = evaluate_with_mappings(
                lookup_code,
                category='verbrauch',
                status_lookup=status_lookup,
                target_lookup=target_lookup,
                formula_obj=formula_obj,
            )
        
        if status is None and ziel is None:
            # Look for separate status and ziel formulas
            try:
                # Try to get status formula (base key)
                status_formula = formula_obj or Formula.objects.get(
                    key=lookup_code, category='verbrauch', is_active=True
                )
                if not status_formula.is_fixed:
                    status = self.evaluator.evaluate(status_formula.expression, use_target=False)
            except (Formula.DoesNotExist, AttributeError):
                pass
            
            try:
                # Try to get ziel formula (key with _ziel suffix)
                ziel_key = f'{lookup_code}_ziel'
                ziel_formula = ziel_formula_obj or Formula.objects.get(
                    key=ziel_key, category='verbrauch', is_active=True
                )
                if not ziel_formula.is_fixed:
                    ziel = self.evaluator.evaluate(ziel_formula.expression, use_target=True)
            except (Formula.DoesNotExist, AttributeError):
                if status is not None:
                    try:
                        status_formula = formula_obj or Formula.objects.get(
                            key=lookup_code, category='verbrauch', is_active=True
                        )
                        if not status_formula.is_fixed:
                            ziel = self.evaluator.evaluate(status_formula.expression, use_target=True)
                    except (Formula.DoesNotExist, AttributeError):
                        pass
        
        # Cache and return
        self.cache[lookup_code] = (status, ziel)
        return status, ziel
    
    def _is_simple_reference(self, formula):
        """Check if formula is a simple code reference"""
        return (
            formula and
            not any(op in formula for op in ['+', '-', '*', '/', '(', ')']) and
            ('.' in formula or formula.startswith('Verbrauch_') or 
             formula.startswith('Renewable_') or formula.startswith('LandUse_'))
        )
    
    def _get_simple_reference_values(self, formula):
        """Get values for simple code references"""
        if formula.startswith('Verbrauch_'):
            lookup_key = formula
        elif formula.startswith('Renewable_'):
            lookup_key = formula
        elif formula.startswith('LandUse_'):
            lookup_key = formula
        else:
            # Standalone code - default to Verbrauch namespace
            lookup_key = f'Verbrauch_{formula}'
        
        status = self.evaluator.status_lookup.get(lookup_key)
        ziel = self.evaluator.target_lookup.get(lookup_key)
        return (status, ziel)
    
    def get_formula(self, code):
        """
        Get the formula for a code.
        Loads from database.
        """
        formula_def = self.formula_service.get_formula(code, category='verbrauch')
        if formula_def:
            return formula_def.get('expression')
        return None
    
    def is_fixed(self, code):
        """
        Check if a code is a fixed value.
        Loads from database.
        """
        formula_def = self.formula_service.get_formula(code, category='verbrauch')
        if formula_def:
            return formula_def.get('is_fixed', True)
        return True
    
    def get_effective_value(self, verbrauch_item):
        """
        Get the effective value considering all calculations.
        
        Args:
            verbrauch_item: The VerbrauchData object
            
        Returns:
            float: The calculated or stored value
        """
        # Check if this item has a formula
        if hasattr(verbrauch_item, 'code'):
            formula_key = f'V_{verbrauch_item.code}'
            if not self.is_fixed(formula_key):
                status, _ = self.calculate(formula_key)
                if status is not None:
                    return status
        
        # Return stored value
        return verbrauch_item.status if hasattr(verbrauch_item, 'status') else None
    
    def get_effective_ziel_value(self, verbrauch_item):
        """
        Get the effective target value considering all calculations.
        
        Args:
            verbrauch_item: The VerbrauchData object
            
        Returns:
            float: The calculated or stored target value
        """
        # Check if this item has a formula
        if hasattr(verbrauch_item, 'code'):
            formula_key = f'V_{verbrauch_item.code}'
            if not self.is_fixed(formula_key):
                _, ziel = self.calculate(formula_key)
                if ziel is not None:
                    return ziel
        
        # Return stored value
        return verbrauch_item.ziel if hasattr(verbrauch_item, 'ziel') else None
