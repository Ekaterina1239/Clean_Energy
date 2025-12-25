# core/services/blockchain_service.py
import hashlib
import json
from datetime import datetime
import requests


class EnergySavingsBlockchain:
    """Блокчейн для верификации сбережений энергии"""

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        """Создание нового блока"""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    def create_transaction(self, building_id, energy_saved, co2_reduced, timestamp):
        """Создание транзакции экономии"""
        transaction = {
            'building_id': building_id,
            'energy_saved_kwh': energy_saved,
            'co2_reduced_kg': co2_reduced,
            'timestamp': timestamp,
            'verified': False
        }

        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1

    def verify_transaction(self, transaction_index):
        """Верификация транзакции (Proof of Saving)"""
        # В реальности будет сложный алгоритм верификации
        # Для демо - простая проверка
        if transaction_index < len(self.current_transactions):
            self.current_transactions[transaction_index]['verified'] = True
            return True
        return False

    @staticmethod
    def hash(block):
        """Хеширование блока"""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """Последний блок в цепи"""
        return self.chain[-1]

    def get_total_savings(self, building_id):
        """Получение общей экономии здания"""
        total_energy = 0
        total_co2 = 0

        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['building_id'] == building_id and transaction['verified']:
                    total_energy += transaction['energy_saved_kwh']
                    total_co2 += transaction['co2_reduced_kg']

        return {
            'total_energy_saved_kwh': total_energy,
            'total_co2_reduced_kg': total_co2,
            'blocks_count': len([b for b in self.chain if any(
                t['building_id'] == building_id for t in b['transactions']
            )])
        }


class CarbonCreditMarket:
    """Рынок углеродных кредитов"""

    def __init__(self):
        self.credits = {}

    def register_savings(self, building_id, co2_reduced):
        """Регистрация сбережений для получения кредитов"""
        if building_id not in self.credits:
            self.credits[building_id] = 0

        # 1 кредит = 1000 кг CO2
        credits_earned = co2_reduced / 1000
        self.credits[building_id] += credits_earned

        return {
            'building_id': building_id,
            'co2_reduced_kg': co2_reduced,
            'credits_earned': credits_earned,
            'total_credits': self.credits[building_id],
            'market_value': self.calculate_market_value(credits_earned)
        }

    def calculate_market_value(self, credits):
        """Расчет рыночной стоимости кредитов"""
        # Текущая цена ~$50 за тонну CO2
        return credits * 50

    def trade_credits(self, from_building, to_building, amount, price):
        """Торговля углеродными кредитами"""
        if self.credits.get(from_building, 0) >= amount:
            self.credits[from_building] -= amount
            self.credits[to_building] = self.credits.get(to_building, 0) + amount

            return {
                'success': True,
                'transaction_id': self.generate_transaction_id(),
                'from': from_building,
                'to': to_building,
                'amount': amount,
                'price': price,
                'total_value': amount * price
            }

        return {'success': False, 'error': 'Insufficient credits'}