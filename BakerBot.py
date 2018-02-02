import hlt
import logging
import itertools
from collections import OrderedDict
game = hlt.Game("BakerBot-V12")
logging.info("Starting BakerBot-V12")

#Author: Mark Baker
#2/1/2018

"""Mine Planet Method:
*If a ship can dock at the input planet, it will return a dock command to input p.
*Else, it will return a navigate to the input planet p
*
"""
def minePlanet(p):
    if ship.can_dock(p):
        return ship.dock(p)
    else:
        return ship.navigate(
            ship.closest_point_to(p),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            max_corrections=90,
            angular_step=5,)

"""Attack Ship Method:
*Will return a navigate command attacking the input enemy ship p
*
"""
def attackShip(p):
    return ship.navigate(
        ship.closest_point_to(p),
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        max_corrections=90,
        angular_step=5,
        ignore_ships=False)

"""Calculating Ship Productivity Method:
*This method will take into account the distance a ship is between the input target and assign it a productivity value. 
*It will do the same with the type of entity the target is and if it is an empty planet or one owned by it
*These productivity values will then be entered into a weighted formula and that value will be returned and assigned to this target

"""
def calculateProductivity(ship, target):
    if ship.calculate_distance_between(target) < 10:
        distanceProductivity = 9
    elif ship.calculate_distance_between(target) < 50:
        distanceProductivity = 10
    elif ship.calculate_distance_between(target) < 100:
        distanceProductivity = 4
    elif ship.calculate_distance_between(target) < 200:
        distanceProductivity = 3
    else:
        distanceProductivity = 2

    if isinstance(target, hlt.entity.Ship):
        typeProductivity = 3
    else:
        if target.owner == game_map.get_me().id:
            typeProductivity = 8
        else:
            typeProductivity = 8
    
    return distanceProductivity * 0.5 + typeProductivity * 0.5


"""Determine Ship Objective Method:
*This method will calculate productivity levels for all entities in the input entities dict.
*It will then sort this into a list and attempt to navigate to/dock at the first entity in the list,
*   the one with the highest productivity value.
*
"""
def determineObjective(ship, entities):
    objectiveImportance = {}
    for r in entities:
        objectiveImportance[r] = calculateProductivity(ship, r)

    sorted(objectiveImportance.items(), key=lambda t:t[1], reverse = True)
    targets = list(objectiveImportance.keys())

    for t in targets:
        if isinstance(t, hlt.entity.Planet):
            if ship.can_dock(t):
                cmd = ship.dock(t)
            else:
                cmd = minePlanet(t)
            return cmd
        elif isinstance(t, hlt.entity.Ship):
            cmd = attackShip(t)
            return cmd
        else:
            logging.info("no command issued")

while True:
    #Instance variable
    game_map = game.update_map()
    command_queue = []
    planned_ships = []
    team_ships = game_map.get_me().all_ships()
    sorted(team_ships, key=lambda ship:ship.id)
    firstTurn = False
    orderedTeamShipsByY = team_ships
    sorted(orderedTeamShipsByY, key=lambda ship:ship.y, reverse = True)
    modelship = team_ships[0]
    modelshipid = team_ships[0].id

    #If the number of team ships is 3, and every ship has the same x coordinate, firstTurn is true, else it is false
    if len(team_ships) == 3:
        for s in team_ships:
            if s.x != modelship.x:
                firstTurn = False
                break
            else:
                firstTurn = True
                continue
    else:
        firstTurn = False
            
    for ship in game_map.get_me().all_ships():
        navigate_command = False
        shipid = ship.id
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        #Taken from Sentdex, returns dict of entities sorted by closest distance
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        
        #Taken from Sentdex
        #closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance 
                                                                        #if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and 
                                                                        #   not entities_by_distance[distance][0].is_owned()]
        #Adapted into:
        #List of valid planet objects(unowned planets, owned planets) sorted by distance
        closest_viable_planets = [entities_by_distance[distance][0] for distance in entities_by_distance 
                                                                        if isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and 
                                                                            (not entities_by_distance[distance][0].is_owned() or 
                                                                            (entities_by_distance[distance][0].is_owned and 
                                                                            entities_by_distance[distance][0].owner.id == game_map.get_me().id and 
                                                                            not entities_by_distance[distance][0].is_full()))]
        
        #Taken from Sentdex, returns sorted list of enemy ships by distance
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance 
                                                                    if isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and 
                                                                        entities_by_distance[distance][0] not in team_ships]

        #Above commands adapated into this monster
        #List of valid planet objects(enemy ships, unowned planets, owned planets) sorted by distance
        closest_valid_entities = [entities_by_distance[distance][0] for distance in entities_by_distance 
                                                                        if ((isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and 
                                                                            (not entities_by_distance[distance][0].is_owned() or 
                                                                            (entities_by_distance[distance][0].is_owned and 
                                                                            entities_by_distance[distance][0].owner.id == game_map.get_me().id and 
                                                                            not entities_by_distance[distance][0].is_full()))) or
                                                                            (isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and
                                                                            entities_by_distance[distance][0] not in team_ships))]

        #If it is the first turn, push ships away from each other. 
        if firstTurn:

            ts = team_ships

            sorted(ts, key=lambda ship: ship.id, reverse=True)

            if ship.id == ts[0].id:
                navigate_command = ship.thrust(
                    int(hlt.constants.MAX_SPEED),
                    180)
                if navigate_command:
                    command_queue.append(navigate_command)
            elif ship.id == ts[1].id:
                navigate_command = ship.thrust(
                    int(hlt.constants.MAX_SPEED),
                    270)
                if navigate_command:
                    command_queue.append(navigate_command)
            elif  ship.id == ts[2].id:
                navigate_command = ship.thrust(
                    int(hlt.constants.MAX_SPEED),
                    90)
                if navigate_command:
                    command_queue.append(navigate_command)
            else:
                navigate_command = ship.thrust(
                    int(hlt.constants.MAX_SPEED),
                    0)
                if navigate_command:
                    command_queue.append(navigate_command)

        #If it is not the first turn
        else:
            if len(closest_enemy_ships) <= 5:

                #If our current ship is the modelship, we try to dock and mine and planet
                if ship.id == modelship.id:
                    if len(closest_viable_planets) > 0:
                        target_planet = closest_viable_planets[0]
                        if ship.can_dock(target_planet):
                            command_queue.append(ship.dock(target_planet))
                        else:
                            navigate_command = minePlanet(target_planet)
                            if navigate_command:
                                command_queue.append(navigate_command) 
                    #Else, we attack
                    else:
                        for tship in closest_enemy_ships:
                            if tship in planned_ships:
                                continue
                            else:
                                navigate_command = attackShip(tship)

                                if navigate_command:
                                    command_queue.append(navigate_command)
                                    break
                #Else, 
                else:
                    #We check the distance between ourselves if the length of team_ships is 3 or above, and navigate if needed
                    if len(team_ships) >= 3:
                        #If we are within 90 units of the closest enemy, compare distance between ships and thrust if needed, so we dont collide
                        if ship.calculate_distance_between(closest_enemy_ships[0]) < 90:
                            for compareShip in team_ships:
                                if ship.id == compareShip.id:
                                    continue
                                elif ship.calculate_distance_between(compareShip) <= 5:
                                    if ship.id == orderedTeamShipsByY[0].id:
                                        navigate_command = ship.thrust(
                                            int(hlt.constants.MAX_SPEED),
                                            120)
                                        if navigate_command:
                                            command_queue.append(navigate_command)
                                            break
                                    elif ship.id == orderedTeamShipsByY[2].id:
                                        navigate_command = ship.thrust(
                                            int(hlt.constants.MAX_SPEED),
                                            300)
                                        if navigate_command:
                                            command_queue.append(navigate_command)
                                            break
                                    else:
                                        navigate_command = ship.thrust(
                                            int(hlt.constants.MAX_SPEED),
                                            180)
                                        if navigate_command:
                                            command_queue.append(navigate_command)
                                            break
                                #Else, we attack
                                else:
                                    for tship in closest_enemy_ships:
                                        if tship in planned_ships:
                                            continue
                                        else:
                                            navigate_command = attackShip(tship)
                                            if navigate_command:
                                                command_queue.append(navigate_command)
                                                break
                                    
                                    break

                        #Else, we implement objective algorithm
                        else:
                            navigate_command = determineObjective(ship, closest_valid_entities)
                            if navigate_command:
                                command_queue.append(navigate_command)
                    #Else, we implement objective algorithm
                    else: 
                        navigate_command = determineObjective(ship, closest_valid_entities)
                        if navigate_command:
                            command_queue.append(navigate_command)
            #Else, we implement objective algorithm
            else: 
                navigate_command = determineObjective(ship, closest_valid_entities)
                if navigate_command:
                    command_queue.append(navigate_command)

    game.send_command_queue(command_queue)
    # TURN END
# GAME END


