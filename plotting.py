import io
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64

sns.set()


def make_cmc_speed_plot(df: pd.DataFrame) -> bytes:
    """
    make a basic plot in memory and then return the base64 encoding to embed in the HTML
    """
    plt.bar(x=df["CMC"], height=df["Card in Library"])
    plt.gca().set_xlabel("Converted Mana Cost")
    plt.gca().set_ylabel("Turns")
    img_handle = io.BytesIO()
    plt.savefig(
        img_handle,
        format="png",
    )
    img_handle.seek(0)
    result = base64.b64encode(img_handle.getvalue())
    img_handle.close()
    return result
