# myapp/serializers.py
# Este arquivo é opcional - vamos criar uma versão simples

class EstabelecimentoSerializer:
    """Serializer simples para Estabelecimento"""
    
    @staticmethod
    def serialize(estabelecimento):
        """Serializa um objeto Estabelecimento para dicionário"""
        return {
            'id': estabelecimento.id,
            'nome_fantasia': estabelecimento.nome_fantasia,
            'razao_social': estabelecimento.razao_social,
            'cnpj': estabelecimento.cnpj,
            'endereco': estabelecimento.endereco,
            'bairro': estabelecimento.bairro,
            'cidade': estabelecimento.cidade,
            'uf': estabelecimento.uf,
            'cep': estabelecimento.cep,
            'bandeira': estabelecimento.bandeira,
            'latitude': estabelecimento.latitude,
            'longitude': estabelecimento.longitude,
            'telefone': estabelecimento.telefone,
        }


class PrecoCombustivelSerializer:
    """Serializer simples para PrecoCombustivel"""
    
    @staticmethod
    def serialize(preco):
        """Serializa um objeto PrecoCombustivel para dicionário"""
        return {
            'id': preco.id,
            'tipo_combustivel': preco.tipo_combustivel,
            'preco': float(preco.preco),
            'data_coleta': preco.data_coleta.strftime('%Y-%m-%d %H:%M:%S') if preco.data_coleta else None,
            'fonte': preco.fonte,
        }