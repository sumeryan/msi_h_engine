from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class MeasurementType(Enum):
    """Tipos de medição disponíveis."""
    CUSTOM = "CUSTOM"      # Período customizado com dias específicos
    MONTHLY = "MENSAL"     # Período mensal (1º ao último dia do mês)


@dataclass
class ContractConfiguration:
    """Configuração do contrato para cálculos de período de medição."""
    measurement_type: MeasurementType
    approval_limit_day: int                    # Ex: 18
    initial_measurement_day: Optional[int] = None  # Ex: 16 (apenas para CUSTOM)
    final_measurement_day: Optional[int] = None    # Ex: 15 (apenas para CUSTOM)
    
    def __post_init__(self):
        """Valida a configuração após inicialização."""
        if self.measurement_type == MeasurementType.CUSTOM:
            if self.initial_measurement_day is None or self.final_measurement_day is None:
                raise ValueError("CUSTOM measurement type requires initial_measurement_day and final_measurement_day")
        elif self.measurement_type == MeasurementType.MONTHLY:
            if self.initial_measurement_day is not None or self.final_measurement_day is not None:
                raise ValueError("MONTHLY measurement type should not have initial_measurement_day or final_measurement_day")


class MeasurementPeriodCalculator:
    """Calculadora para determinar períodos de medição baseada em configurações de contrato."""
    
    def __init__(self, config: ContractConfiguration):
        self.config = config
    
    def _add_months(self, date: datetime, months: int) -> datetime:
        """
        Adiciona meses a uma data usando datetime nativo.
        
        Args:
            date: Data de origem
            months: Número de meses a adicionar
            
        Returns:
            datetime: Nova data com meses adicionados
        """
        month = date.month + months
        year = date.year
        
        # Lidar com overflow de ano
        while month > 12:
            month -= 12
            year += 1
        
        # Lidar com underflow de ano
        while month < 1:
            month += 12
            year -= 1
            
        return date.replace(year=year, month=month)
    
    def _subtract_months(self, date: datetime, months: int) -> datetime:
        """
        Subtrai meses de uma data usando datetime nativo.
        
        Args:
            date: Data de origem
            months: Número de meses a subtrair
            
        Returns:
            datetime: Nova data com meses subtraídos
        """
        return self._add_months(date, -months)
    
    def _get_last_day_of_month(self, date: datetime) -> int:
        """
        Obtém o último dia do mês de uma data específica.
        
        Args:
            date: Data de referência
            
        Returns:
            int: Último dia do mês
        """
        # Vai para o primeiro dia do próximo mês e subtrai um dia
        if date.month == 12:
            next_month_first_day = date.replace(year=date.year + 1, month=1, day=1)
        else:
            next_month_first_day = date.replace(month=date.month + 1, day=1)
        
        last_day_of_month = next_month_first_day - timedelta(days=1)
        return last_day_of_month.day
        
    def _get_period_for_execution_date(self, execution_date: datetime) -> tuple[datetime, datetime, datetime]:
        """
        Calcula o período de medição baseado na data de execução.
        
        Args:
            execution_date: Data em que o lançamento foi executado
            
        Returns:
            tuple: (inicio_periodo, fim_periodo, limite_aprovacao)
        """
        if self.config.measurement_type == MeasurementType.MONTHLY:
            return self._get_monthly_period(execution_date)
        else:  # CUSTOM
            return self._get_custom_period(execution_date)
    
    def _get_monthly_period(self, execution_date: datetime) -> tuple[datetime, datetime, datetime]:
        """
        Calcula período de medição MENSAL baseado na data de execução.
        
        Args:
            execution_date: Data em que o lançamento foi executado
            
        Returns:
            tuple: (inicio_periodo, fim_periodo, limite_aprovacao)
        """
        # Para medição mensal, o período é sempre do primeiro ao último dia do mês
        period_start = execution_date.replace(day=1)
        
        # Último dia do mês
        last_day = self._get_last_day_of_month(execution_date)
        period_end = execution_date.replace(day=last_day)
        
        # Limite de aprovação é no próximo mês
        next_month = self._add_months(execution_date.replace(day=1), 1)
        approval_limit = next_month.replace(day=self.config.approval_limit_day)
        
        return period_start, period_end, approval_limit
    
    def _get_custom_period(self, execution_date: datetime) -> tuple[datetime, datetime, datetime]:
        """
        Calcula período de medição CUSTOM baseado na data de execução.
        
        Args:
            execution_date: Data em que o lançamento foi executado
            
        Returns:
            tuple: (inicio_periodo, fim_periodo, limite_aprovacao)
        """
        # Determinar mês/ano de referência baseado na data de execução
        if execution_date.day >= self.config.initial_measurement_day:
            # Se a execução foi no dia inicial ou depois, o período é do mês atual
            reference_month = execution_date.replace(day=1)
        else:
            # Se foi antes do dia inicial, o período é do mês anterior
            reference_month = self._subtract_months(execution_date.replace(day=1), 1)
        
        # Calcular início do período (dia inicial do mês de referência)
        period_start = reference_month.replace(day=self.config.initial_measurement_day)
        
        # Calcular fim do período (dia final do próximo mês)
        next_month = self._add_months(reference_month, 1)
        period_end = next_month.replace(day=self.config.final_measurement_day)
        
        # Calcular limite de aprovação (baseado no mês do fim do período)
        approval_limit = next_month.replace(day=self.config.approval_limit_day)
        
        return period_start, period_end, approval_limit
    
    def _get_next_period(self, current_period_end: datetime) -> tuple[datetime, datetime]:
        """
        Calcula o próximo período de medição baseado no fim do período atual.
        
        Args:
            current_period_end: Data final do período atual
            
        Returns:
            tuple: (inicio_proximo_periodo, fim_proximo_periodo)
        """
        # O próximo período inicia no dia seguinte ao fim do período atual
        next_start = current_period_end + timedelta(days=1)
        next_start_date, next_end_date, _ = self._get_period_for_execution_date(next_start)
        
        return next_start_date, next_end_date
    
    def calculate_measurement_period(self, 
                                   execution_date: datetime, 
                                   approval_date: datetime) -> Dict[str, Any]:
        """
        Calcula o período de medição e determina se o lançamento deve ser incluído.
        
        Args:
            execution_date: Data em que o lançamento foi executado
            approval_date: Data em que o lançamento foi aprovado
            
        Returns:
            Dict: {
                "is_next": bool,
                "start_date": datetime,
                "end_date": datetime
            }
        """
        # Obter período baseado na data de execução
        period_start, period_end, approval_limit = self._get_period_for_execution_date(execution_date)
        
        # Verificar se a execução está dentro do período calculado
        if not (period_start <= execution_date <= period_end):
            raise ValueError(
                f"Execution date {execution_date.strftime('%Y-%m-%d')} "
                f"is not within calculated period "
                f"({period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')})"
            )
        
        # Determinar se deve incluir na medição atual
        if approval_date <= approval_limit:
            # Incluir no período atual
            return {
                "is_next": False,
                "start_date": period_start,
                "end_date": period_end
            }
        else:
            # Incluir no próximo período
            next_start, next_end = self._get_next_period(period_end)
            return {
                "is_next": True,
                "start_date": next_start,
                "end_date": next_end
            }

# Exemplos de uso (podem ser removidos em produção)
def example_usage():
    """Demonstra o uso do módulo com exemplos práticos."""
    
    print("=== EXEMPLO 1: CONFIGURAÇÃO CUSTOM ===")
    # Configuração do contrato CUSTOM (exemplo original)
    config_custom = ContractConfiguration(
        measurement_type=MeasurementType.CUSTOM,
        initial_measurement_day=16,
        final_measurement_day=15,
        approval_limit_day=18
    )
    
    calculator_custom = MeasurementPeriodCalculator(config_custom)
    
    # Caso de teste: execução dentro do período, aprovação dentro do limite
    result_custom = calculator_custom.calculate_measurement_period(
        execution_date=datetime(2025, 7, 16),
        approval_date=datetime(2025, 7, 16)
    )
    
    print(f"CUSTOM - is_next: {result_custom['is_next']}")
    print(f"CUSTOM - start_date: {result_custom['start_date'].strftime('%Y-%m-%d')}")
    print(f"CUSTOM - end_date: {result_custom['end_date'].strftime('%Y-%m-%d')}")
    print()
    
    print("=== EXEMPLO 2: CONFIGURAÇÃO MENSAL ===")
    # Configuração do contrato MENSAL
    config_monthly = ContractConfiguration(
        measurement_type=MeasurementType.MONTHLY,
        approval_limit_day=5  # Limite de aprovação no dia 5 do próximo mês
    )
    
    calculator_monthly = MeasurementPeriodCalculator(config_monthly)
    
    # Caso de teste: execução em março, aprovação dentro do limite (abril)
    result_monthly = calculator_monthly.calculate_measurement_period(
        execution_date=datetime(2024, 3, 15),
        approval_date=datetime(2024, 4, 3)  # Aprovado antes do dia 5 de abril
    )
    
    print(f"MONTHLY - is_next: {result_monthly['is_next']}")
    print(f"MONTHLY - start_date: {result_monthly['start_date'].strftime('%Y-%m-%d')}")
    print(f"MONTHLY - end_date: {result_monthly['end_date'].strftime('%Y-%m-%d')}")
    print()
    
    # Caso de teste: execução em março, aprovação fora do limite
    result_monthly_late = calculator_monthly.calculate_measurement_period(
        execution_date=datetime(2024, 3, 15),
        approval_date=datetime(2024, 4, 10)  # Aprovado depois do dia 5 de abril
    )
    
    print(f"MONTHLY LATE - is_next: {result_monthly_late['is_next']}")
    print(f"MONTHLY LATE - start_date: {result_monthly_late['start_date'].strftime('%Y-%m-%d')}")
    print(f"MONTHLY LATE - end_date: {result_monthly_late['end_date'].strftime('%Y-%m-%d')}")
    
    return result_custom, result_monthly, result_monthly_late


if __name__ == "__main__":
    results = example_usage()
    for result in results:
        print(result)