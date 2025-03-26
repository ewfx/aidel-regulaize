# Update the _calculate_relationship_risk method in PipelineService

async def _calculate_relationship_risk(self, entity_id: str) -> float:
    """Calculate risk score based on entity relationships"""
    try:
        # Get entity connections from graph database
        connections = await self.graph_store.get_entity_connections(str(entity_id))
        
        if not connections:
            return 0.0
        
        # Calculate risk based on connected entities
        risk_scores = []
        for connection in connections:
            if connection.get('risk_score') is not None:
                # Weight risk score by distance (closer connections have more impact)
                distance_weight = 1.0 / connection['distance']
                weighted_risk = float(connection['risk_score']) * distance_weight
                risk_scores.append(weighted_risk)
        
        # Return maximum weighted risk score or 0 if no valid scores
        return max(risk_scores) if risk_scores else 0.0

    except Exception as e:
        logger.error(f"Error calculating relationship risk: {str(e)}")
        return 0.0