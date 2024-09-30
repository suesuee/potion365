import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ Updates the inventory based on delivered barrels. """
    
    # Fetch the data first to ensure we are not overwriting the existing values.
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions, num_green_ml, gold FROM global_inventory WHERE id = 1"
        ))
        row = result.first()
        cur_num_green_potions = row['num_green_potions']
        cur_num_green_ml = row['num_green_ml']
        cur_gold = row['gold']

        for barrel in barrels_delivered:
            if "GREEN" in barrel.sku.upper():
                cur_num_green_ml += barrel.ml_per_barrel * barrel.quantity
                cur_gold -= barrel.price * barrels_delivered

                connection.execute(sqlalchemy.text(
                    "UPDATE global_inventory SET num_green_ml={cur_num_green_ml}, gold={cur_gold} FROM global_inventory WHERE id = 1"
                ))

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ Purchase a new barrel if the potion inventory is low. """
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions, num_green_ml, gold FROM global_inventory WHERE id = 1"
        ))
    row = result.first()
    cur_num_green_potions = row['num_green_potions']
    cur_num_green_ml = row['num_green_ml']
    cur_gold = row['gold']

    # Purchase a new small green potion barrel only if the number of potions in inventory is less than 10
    for barrel in wholesale_catalog:
        if "GREEN" in barrel.sku.upper() and cur_num_green_potions < 10 and cur_gold >= barrel.price:
            return [
            {
                "sku": "SMALL_GREEN_BARREL",
                "quantity": 1,
            }
        ]
    return [] # Retrun an empty plan if purchase is not needed

